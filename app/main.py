from naoqi import ALProxy, ALModule, ALBroker
import urllib2
import json
import time
import threading
import requests
import paramiko

ROBOT_IP = "192.168.15.119"

def get_story(messages):
    """Get story from the server based on given messages."""
    data = json.dumps({'messages': messages})
    request = urllib2.Request('http://localhost:5000/generate_story', data, {'Content-Type': 'application/json'})
    response = urllib2.urlopen(request)
    story = response.read()
    return story

def send_question_to_server(question):
    """Send user question to the server and get the answer."""
    prompt.append({"role": "user", "content": question})
    answer = get_story(prompt)
    prompt.append({"role": "assistant", "content": answer})
    return answer

def perform_gesture(motion_proxy, gesture):
    """Perform gestures based on the emotion in the sentence."""
    print("Gesture given:", gesture)

    if gesture == 'happy':
        names = ["LShoulderPitch", "LShoulderRoll", "LElbowYaw", "LElbowRoll", "RShoulderPitch", "RShoulderRoll", "RElbowYaw", "RElbowRoll", "HeadYaw", "HeadPitch"]
        angles = [0.0, 0.3, -1.5, -0.5, 0.0, -0.3, 1.5, 0.5, 0.0, -0.2]
        times = [1.0] * len(names)
        motion_proxy.angleInterpolation(names, angles, times, True)

        angles = [0.5, -0.3, 1.5, 0.5, 0.5, 0.3, -1.5, -0.5, 0.0, 0.2]
        motion_proxy.angleInterpolation(names, angles, times, True)

        angles = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        motion_proxy.angleInterpolation(names, angles, times, True)

    elif gesture == "sad":
        names = ["LShoulderPitch", "RShoulderPitch", "HeadYaw", "HeadPitch"]
        angles = [1.5, 1.5, 0.0, 0.5]
        times = [1.0] * len(names)
        motion_proxy.angleInterpolation(names, angles, times, True)

    elif gesture == "excited":
        names = ["LShoulderPitch", "LShoulderRoll", "LElbowYaw", "LElbowRoll", "RShoulderPitch", "RShoulderRoll", "RElbowYaw", "RElbowRoll", "HeadYaw", "HeadPitch"]
        angles = [0.0, 0.3, -1.5, -0.5, 0.0, -0.3, 1.5, 0.5, 0.0, -0.2]
        times = [0.5] * len(names)
        motion_proxy.angleInterpolation(names, angles, times, True)

        angles = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        motion_proxy.angleInterpolation(names, angles, times, True)


def tell_story(sentences, event_listener):
    """Tell the story with possible interruptions and gestures."""
    for i, sentence in enumerate(sentences):
        print(sentence)

        if event_listener.interrupted.is_set():
            print("Storytelling was interrupted.")
            event_listener.current_sentence_index = i
            break

        gesture_thread = None

        if "happy" in sentence.lower():
            gesture_thread = threading.Thread(target=perform_gesture, args=(event_listener.motion, "happy"))
        elif "sad" in sentence.lower():
            gesture_thread = threading.Thread(target=perform_gesture, args=(event_listener.motion, "sad"))
        elif "excited" in sentence.lower():
            gesture_thread = threading.Thread(target=perform_gesture, args=(event_listener.motion, "excited"))

        # Start gesture thread so that it can run in parallel with speech instead of waiting for it to finish
        if gesture_thread:
            gesture_thread.start()

        event_listener.tts.say(sentence)

        # Wait for gesture thread to finish before continuing to the next sentence
        if gesture_thread:
            gesture_thread.join()

        time.sleep(1)

    if event_listener.interrupted.is_set():
        question = event_listener.listen_for_question(5)
        print("Question received:", question)
        answer = send_question_to_server(question)
        print("Answer:", answer)
        event_listener.tts.say(answer)
        event_listener.interrupted.clear()
        event_listener.memory.subscribeToEvent("WordRecognized", "speech_listener", "on_word_recognized")
        tell_story(sentences[(event_listener.current_sentence_index - 1):], event_listener)


class SpeechEventListener(ALModule):
    """Event listener class for handling speech events."""
    def __init__(self, name, robot_ip, port):
        ALModule.__init__(self, name)
        self.memory = ALProxy("ALMemory", robot_ip, port)
        self.tts = ALProxy("ALTextToSpeech", robot_ip, port)
        self.asr = ALProxy("ALSpeechRecognition", robot_ip, port)
        self.audio_recorder = ALProxy("ALAudioRecorder", robot_ip, port)
        self.motion = ALProxy("ALMotion", robot_ip, port)
        self.motion.setStiffnesses("Body", 1.0)
        self.posture = ALProxy("ALRobotPosture", robot_ip, port)
        self.posture.goToPosture("StandInit", 0.5)
        self.memory.subscribeToEvent("WordRecognized", "speech_listener", "on_word_recognized")
        self.interrupted = threading.Event()
        self.current_sentence_index = 0

    def on_word_recognized(self, key, value, message):
        """Handle recognized words and possibly interrupt storytelling."""
        print(value)

        if value and value[0] in ['stop', 'pause', 'wait'] and value[1] > 0.4:
            print("Interrupted by keyword: ", value[0])
            self.interrupted.set()
            self.tts.stopAll()
            self.memory.unsubscribeToEvent("WordRecognized", self.getName())

    def listen_for_question(self, duration):
        """Record and transcribe user question."""
        audio_path = "/home/nao/audio/testtest.wav"

        try:
            self.audio_recorder.stopMicrophonesRecording()
        except:
            pass

        self.audio_recorder.startMicrophonesRecording(audio_path, "wav", 16000, [0, 0, 1, 0])
        print("Recording audio for question")
        time.sleep(duration)
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
        sftp.close()
        transport.close()

        audio_path = '/home/suryansh/git/comp3018/file.wav'
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
            print("Error occurred while sending the audio file:", e)

        return transcription

    def start_listening(self, keywords):
        """Start listening for specific keywords."""
        print("Start listening")
        self.asr.pause(True)
        self.asr.setLanguage("English")
        self.asr.setVocabulary(keywords, False)
        self.asr.pause(False)
        self.asr.subscribe("StoryInterruptions")

    def stop_listening(self):
        """Stop listening for specific keywords."""
        print("Stop listening")
        self.asr.unsubscribe("StoryInterruptions")

if __name__ == "__main__":
    # Set robot IP and port
    robot_ip = '10.188.220.47'
    port = 9559

    # Set up NAOqi broker and modules
    global myBroker
    myBroker = ALBroker("myBroker", "0.0.0.0", 0, robot_ip, port)

    global speech_listener
    speech_listener = SpeechEventListener("speech_listener", robot_ip, port)

    global story
    global prompt

    # Prompt for openai to generate a story and ask for the topi
    prompt = [
        {"role": "system", "content": "You are a story-telling assistant. You will tell me a story about a topic in 10 sentences that should include the words happy, sad and excited. Ask me what topic the story is about and then continue with the story from there. When you are asked questions about the story you will answer concisely and return to the story. If the question is not about the story then ignore it and return nothing. Only return text and nothing else."}
    ]

    # Get the topic of the story from the user
    response = get_story(prompt)
    prompt.append({"role": "assistant", "content": response})
    speech_listener.tts.say(response)
    topic = speech_listener.listen_for_question(10)
    prompt.append({"role": "user", "content": topic})
    speech_listener.tts.say("Hmmm. Let me think")

    # Generate the story based on the topic
    story = get_story(prompt)
    prompt.append({"role": "assistant", "content": story})

    # Start listening for keywords to interrupt the story
    speech_listener.start_listening(['stop', 'pause', 'wait'])

    story_thread = threading.Thread(target=tell_story, args=(story.split('.'), speech_listener))

    # Start the reading the story on it's own thread so that it can be constantly listening and be interrupted by the keyword recognition
    story_thread.start()

    # Wait for the story thread to finish before continuing
    story_thread.join()

    speech_listener.stop_listening()
    myBroker.shutdown()

    print("Prompt was", prompt)