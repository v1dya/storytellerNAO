from flask import Flask, request, jsonify
from openai import OpenAI

client = OpenAI()

app = Flask(__name__)

@app.route('/transcribe', methods=['POST'])
def transcribe_audio():
    audio_path = request.json['audio_path']

    with open(audio_path, 'rb') as file:
        transcript = client.audio.transcriptions.create(
            model="whisper-1",
            file=file
        )

    return jsonify(transcript.text)

@app.route('/generate_story', methods=['POST'])
def generate_story():
    prompt = request.json['messages']
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=prompt,
        temperature=0.0,
    )

    return jsonify(response.choices[0].message.content)

if __name__ == '__main__':
    app.run(port=5000)
