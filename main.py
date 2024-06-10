import os
import time
import base64
import pyautogui
from PIL import Image
import requests
from dotenv import load_dotenv
import simpleaudio as sa
from pynput import keyboard

# Cargar la clave de API desde el archivo .env
load_dotenv()
api_key = os.getenv('OPENAI_API_KEY')

# Asegurar que las carpetas 'images' y 'audio' existen
if not os.path.exists('images'):
    os.makedirs('images')
if not os.path.exists('audio'):
    os.makedirs('audio')

# Función para capturar la pantalla, redimensionar y guardar la imagen
def capture_screen():
    try:
        screenshot = pyautogui.screenshot()
        resized_screenshot = screenshot.resize((512, 512), Image.LANCZOS)
        if resized_screenshot.mode == 'RGBA':
            resized_screenshot = resized_screenshot.convert('RGB')
        timestamp = int(time.time())
        file_name = f"images/screenshot_{timestamp}.jpg"
        resized_screenshot.save(file_name, "JPEG")
        print(f"Image saved: {file_name}")
        return file_name
    except Exception as e:
        print(f"Error capturing screen: {e}")

# Función para codificar la imagen en base64
def encode_image(image_path):
    try:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    except Exception as e:
        print(f"Error encoding image: {e}")

# Función para analizar la imagen usando la API de OpenAI
def analyze_image(image_path):
    try:
        encoded_image = encode_image(image_path)
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        message = {
            "role": "user",
            "content": [
                {"type": "text", "text": "Si ves una pregunta respondela de manera breve"},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpg;base64,{encoded_image}",
                        "detail": "low"
                    }
                }
            ]
        }
        payload = {
            "model": "gpt-4o",
            "temperature": 0,
            "messages": [message],
            "max_tokens": 300
        }
        response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
        return response.json()
    except Exception as e:
        print(f"Error analyzing image: {e}")

# Función para convertir texto a audio usando la API de OpenAI y reproducirlo
def text_to_speech(text):
    try:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
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

# Función principal para capturar y analizar la imagen, luego convertir el resultado en audio
def main():
    try:
        image_path = capture_screen()
        if image_path:
            response = analyze_image(image_path)
            response_text = response.get("choices")[0].get("message").get("content")
            print(f"Analysis result: {response_text}")
            text_to_speech(response_text)
    except Exception as e:
        print(f"Error in main: {e}")

# Variables globales para gestionar la combinación de teclas
current_keys = set()

# Función para manejar eventos de teclado
def on_press(key):
    try:
        current_keys.add(key)
        if keyboard.Key.ctrl_l in current_keys or keyboard.Key.ctrl_r in current_keys:
            if keyboard.Key.space in current_keys:
                print("Activado.")
                main()
                current_keys.clear()
    except Exception as e:
        print(f"Error on_press: {e}")

def on_release(key):
    try:
        current_keys.discard(key)
    except Exception as e:
        print(f"Error on_release: {e}")

# Escuchar eventos de teclado
def start_listener():
    with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
        listener.join()

print("Presiona 'Ctrl + Espacio' para activar la función.")
start_listener()

