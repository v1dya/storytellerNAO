import pytest
from unittest.mock import patch, Mock
from app import (
    get_story, send_question_to_server, perform_gesture, 
    tell_story, SpeechEventListener
)
import urllib2
import json
import threading
import time

# Test get_story function
def test_get_story():
    messages = [{"role": "user", "content": "Tell me a story about a happy robot"}]
    expected_story = "Once upon a time, there was a happy robot."

    with patch('urllib2.urlopen') as mock_urlopen:
        mock_response = Mock()
        mock_response.read.return_value = expected_story
        mock_urlopen.return_value = mock_response
        
        result = get_story(messages)
        assert result == expected_story
        mock_urlopen.assert_called_once()
        assert mock_urlopen.call_args[0][0].data == json.dumps({'messages': messages}).encode()

# Test send_question_to_server function
def test_send_question_to_server():
    question = "What is the robot's name?"
    prompt = [
        {"role": "system", "content": "You are a story-telling assistant."},
        {"role": "assistant", "content": "Tell me a story about a happy robot."}
    ]
    expected_answer = "The robot's name is Robo."

    with patch('your_module.get_story') as mock_get_story:
        mock_get_story.return_value = expected_answer
        
        result = send_question_to_server(question)
        assert result == expected_answer
        mock_get_story.assert_called_once()

# Test perform_gesture function
def test_perform_gesture():
    motion_proxy = Mock()
    gesture = 'happy'
    perform_gesture(motion_proxy, gesture)
    motion_proxy.angleInterpolation.assert_called()

# Test tell_story function
def test_tell_story():
    sentences = ["This is a happy sentence.", "This is a sad sentence.", "This is an excited sentence."]
    event_listener = Mock()
    event_listener.interrupted.is_set.return_value = False
    event_listener.tts.say = Mock()

    tell_story(sentences, event_listener)
    assert event_listener.tts.say.call_count == len(sentences)

# Test on_word_recognized method in SpeechEventListener
def test_on_word_recognized():
    listener = SpeechEventListener("test_listener", "127.0.0.1", 9559)
    listener.tts = Mock()
    listener.memory = Mock()
    listener.interrupted = threading.Event()

    listener.on_word_recognized("WordRecognized", ["stop", 0.5], "message")
    assert listener.interrupted.is_set()
    listener.tts.stopAll.assert_called_once()
    listener.memory.unsubscribeToEvent.assert_called_once()

# Test listen_for_question method in SpeechEventListener
def test_listen_for_question():
    listener = SpeechEventListener("test_listener", "127.0.0.1", 9559)
    listener.audio_recorder = Mock()
    listener.audio_recorder.stopMicrophonesRecording = Mock()
    listener.audio_recorder.startMicrophonesRecording = Mock()
    
    with patch('paramiko.Transport') as mock_transport, patch('paramiko.SFTPClient.from_transport') as mock_sftp_client, patch('requests.post') as mock_post:
        mock_transport.return_value.connect = Mock()
        mock_sftp_client.return_value.get = Mock()
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {"transcription": "What is your name?"}

        result = listener.listen_for_question(5)
        assert result == {"transcription": "What is your name?"}
        listener.audio_recorder.startMicrophonesRecording.assert_called_once()
        listener.audio_recorder.stopMicrophonesRecording.assert_called_once()

# Test start_listening method in SpeechEventListener
def test_start_listening():
    listener = SpeechEventListener("test_listener", "127.0.0.1", 9559)
    listener.asr = Mock()
    keywords = ['stop', 'pause', 'wait']
    
    listener.start_listening(keywords)
    listener.asr.setVocabulary.assert_called_once_with(keywords, False)
    listener.asr.subscribe.assert_called_once_with("StoryInterruptions")

# Test stop_listening method in SpeechEventListener
def test_stop_listening():
    listener = SpeechEventListener("test_listener", "127.0.0.1", 9559)
    listener.asr = Mock()
    
    listener.stop_listening()
    listener.asr.unsubscribe.assert_called_once_with("StoryInterruptions")
