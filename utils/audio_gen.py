from gtts import gTTS
import os
import uuid

def generate_audio(text, lang='en'):
    filename = f"{uuid.uuid4().hex}.mp3"
    filepath = os.path.join("static", "audio", filename)

    tts = gTTS(text=text, lang=lang)
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    tts.save(filepath)

    return filepath
