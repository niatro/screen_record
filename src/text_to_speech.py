import requests
import simpleaudio as sa
import os
import time

def text_to_speech(text, openai_api_key):
    try:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {openai_api_key}"
        }
        payload = {
            "model": "tts-1",
            "voice": "alloy",
            "input": text,
            "response_format": "wav"
        }
        response = requests.post("https://api.openai.com/v1/audio/speech", headers=headers, json=payload)
        audio_file_path = os.path.join('audio', f"response_{int(time.time())}.wav")
        
        # Guardar el archivo de audio
        with open(audio_file_path, 'wb') as audio_file:
            audio_file.write(response.content)
        
        # Reproducir el archivo de audio
        wave_obj = sa.WaveObject.from_wave_file(audio_file_path)
        play_obj = wave_obj.play()
        play_obj.wait_done()
    except Exception as e:
        print(f"Error in text_to_speech: {e}")
