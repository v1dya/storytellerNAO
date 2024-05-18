from naoqi import ALProxy, ALModule, ALBroker
import motion
import urllib2
import json
import time
import threading
import os
import requests
import paramiko

ROBOT_IP="192.168.15.119"

def get_story(messages):
    data = json.dumps({'messages': messages})
    request = urllib2.Request('http://localhost:5000/generate_story', data, {'Content-Type': 'application/json'})
    response = urllib2.urlopen(request)
    story = response.read()
    return story

def send_question_to_server(question):
    
    prompt.append(
        {"role": "user", "content": question}
    )

    answer = get_story(prompt)
    prompt.append(
        {"role": "assistant", "content": answer}
    )
    return answer

def perform_gesture(motion_proxy, gesture):
    print("Gesture given:", gesture)
    
    if gesture == 'happy':
    # Happy gesture involves raising both arms and possibly moving the head
        names = ["LShoulderPitch", "LShoulderRoll", "LElbowYaw", "LElbowRoll", "RShoulderPitch", "RShoulderRoll", "RElbowYaw", "RElbowRoll", "HeadYaw", "HeadPitch"]
        angles = [0.0, 0.3, -1.5, -0.5, 0.0, -0.3, 1.5, 0.5, 0.0, -0.2]  # Adjust these angles for a more expressive gesture
        times = [1.0] * len(names)
        motion_proxy.angleInterpolation(names, angles, times, True)

        # Add a second part to the gesture, like moving the arms back down with a wave
        angles = [0.5, -0.3, 1.5, 0.5, 0.5, 0.3, -1.5, -0.5, 0.0, 0.2]
        times = [1.0] * len(names)
        motion_proxy.angleInterpolation(names, angles, times, True)

        # Return to a neutral pose
        angles = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        times = [1.0] * len(names)
        motion_proxy.angleInterpolation(names, angles, times, True)

    elif gesture == "sad":
        names = ["LShoulderPitch", "RShoulderPitch", "HeadYaw", "HeadPitch"]
        angles = [1.5, 1.5, 0.0, 0.5]
        times = [1.0] * len(names)
        motion_proxy.angleInterpolation(names, angles, times, True)

    elif gesture == "excited":
        names = ["LShoulderPitch", "LShoulderRoll", "LElbowYaw", "LElbowRoll", "RShoulderPitch", "RShoulderRoll", "RElbowYaw", "RElbowRoll", "HeadYaw", "HeadPitch"]
        angles = [0.0, 0.3, -1.5, -0.5, 0.0, -0.3, 1.5, 0.5, 0.0, -0.2]  # Adjust these angles for a more expressive gesture
        times = [0.5] * len(names)
        motion_proxy.angleInterpolation(names, angles, times, True)

        # Return to a neutral pose
        angles = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        times = [0.5] * len(names)
        motion_proxy.angleInterpolation(names, angles, times, True)


def tell_story(sentences, event_listener):
    for i, sentence in enumerate(sentences):
        print(sentence)
        if event_listener.interrupted.is_set():
            print("Storytelling was interrupted.")
            event_listener.current_sentence_index = i
            break

        # Perform a gesture after each sentence
        gesture_thread = None
        if "happy" in sentence.lower():
            gesture_thread = threading.Thread(target=perform_gesture, args=(event_listener.motion, "happy"))
        elif "sad" in sentence.lower():
            gesture_thread = threading.Thread(target=perform_gesture, args=(event_listener.motion, "sad"))
        elif "excited" in sentence.lower():
            gesture_thread = threading.Thread(target=perform_gesture, args=(event_listener.motion, "excited"))

        if gesture_thread:
            gesture_thread.start()

        event_listener.tts.say(sentence)

        if gesture_thread:
            gesture_thread.join()

        time.sleep(1)  # Sleep briefly to allow interruption checks

    if event_listener.interrupted.is_set():
        question = event_listener.listen_for_question(5)
        print("Question received:",question)
        answer = send_question_to_server(question)
        print("Answer:",answer)
        event_listener.tts.say(answer)
        event_listener.interrupted.clear()
        event_listener.memory.subscribeToEvent("WordRecognized", "speech_listener", "on_word_recognized")
        tell_story(sentences[(event_listener.current_sentence_index - 1):], event_listener)

class SpeechEventListener(ALModule):
    def __init__(self, name, robot_ip, port):
        ALModule.__init__(self, name)
        self.memory = ALProxy("ALMemory", robot_ip, port)
        self.tts = ALProxy("ALTextToSpeech", robot_ip, port)
        self.asr = ALProxy("ALSpeechRecognition", robot_ip, port)
        self.audio_recorder = ALProxy("ALAudioRecorder", robot_ip, port)
        self.motion = ALProxy("ALMotion", robot_ip, port)
        self.motion.setStiffnesses("Body", 1.0)  # Enable stiffness for the whole body
        self.posture = ALProxy("ALRobotPosture", robot_ip, port)  # Added posture proxy
        self.posture.goToPosture("StandInit", 0.5)    
        self.memory.subscribeToEvent("WordRecognized", "speech_listener", "on_word_recognized")
        self.interrupted = threading.Event()
        self.current_sentence_index = 0

    def on_word_recognized(self, key, value, message):
        print(value)
        if value and value[0] in ['stop', 'pause', 'wait'] and value[1] > 0.4:  # Adjust confidence level as needed
            print("Interrupted by keyword: ", value[0])
            self.interrupted.set()
            self.tts.stopAll()  # Stop the robot's speech immediately
            self.memory.unsubscribeToEvent("WordRecognized", self.getName())

    def listen_for_question(self, duration):
        audio_path = "/home/nao/audio/testtest.wav"  # Adjust path as needed

        try:
            self.audio_recorder.stopMicrophonesRecording()
        except:
            pass


        self.audio_recorder.startMicrophonesRecording(audio_path, "wav", 16000, [0, 0, 1, 0])
        print("Recording audio for question")
        time.sleep(duration)  # Adjust the recording time as needed
        self.audio_recorder.stopMicrophonesRecording()
        print("Finished recording audio")

        host = '10.188.220.47'
        user = 'nao'
        password = 'nao'
        filename = audio_path

        
        transport = paramiko.Transport((host, 22))
        transport.connect(username=user, password=password)
        sftp = paramiko.SFTPClient.from_transport(transport)
        sftp.get(filename, '/home/suryansh/git/comp3018/file.wav')
        print("File downloaded successfully.")

        audio_path='/home/suryansh/git/comp3018/file.wav'


        sftp.close()
        transport.close()

        url = 'http://localhost:5000/transcribe'

        try:
            response = requests.post(url, json={'audio_path': audio_path})

            if response.status_code == 200:
                print("Response is", response.json())
                transcription = str(response.json())
                print("Transcription received:", transcription)
            else:
                transcription = ''
                print("Failed to get transcription. Status code:", response.status_code)
        except Exception as e:
            transcription = ''
            print("Error occurred while sending the audio file:",e)

        return transcription

    def start_listening(self, keywords):
        print("Start listening")
        self.asr.pause(True)  # Pause the ASR engine
        self.asr.setLanguage("English")
        self.asr.setVocabulary(keywords, False)
        self.asr.pause(False)  # Unpause the ASR to apply the vocabulary changes
        self.asr.subscribe("StoryInterruptions")

    def stop_listening(self):
        print("Stop listening")
        self.asr.unsubscribe("StoryInterruptions")

if __name__ == "__main__":
    # robot_ip = '192.168.15.124'
    robot_ip = '10.188.220.47'
    port = 9559

    # Setting up NAOqi broker and modules
    global myBroker
    myBroker = ALBroker("myBroker", "0.0.0.0", 0, robot_ip, port)

    global speech_listener
    speech_listener = SpeechEventListener("speech_listener", robot_ip, port)
    
    global story
    global prompt
    prompt = [
        {"role": "system", "content": "You are a story-telling assistant. You will tell me a story about a topic in 10 sentences that should include the words happy, sad and excited. Ask me what topic the story is about and then continue with the story from there. When you are asked questions about the story you will answer concisely and return to the story. If the question is not about the story then ignore it and return nothing. Only return text and nothing else."}
    ]

    response = get_story(prompt)
    prompt.append(
        {"role": "assistant", "content": response}
    )

    speech_listener.tts.say(response)

    topic = speech_listener.listen_for_question(10)
    
    prompt.append(
        {"role": "user", "content": topic}
    )

    speech_listener.tts.say("Hmmm. Let me think")
    story = get_story(prompt)

    prompt.append(
        {"role": "assistant", "content": story}
    )
    speech_listener.start_listening(['stop', 'pause', 'wait'])
    story_thread = threading.Thread(target=tell_story, args=(story.split('.'), speech_listener))

    story_thread.start()
    story_thread.join()  # Wait for the story to finish or be interrupted

    speech_listener.stop_listening()
    myBroker.shutdown()

    print("Prompt was", prompt)