import os
import time
import base64
import pyautogui
from PIL import Image
import requests
from dotenv import load_dotenv
import simpleaudio as sa
from pynput import keyboard
from anthropic import Anthropic
import threading
import signal
import sys

# Cargar claves de API desde el archivo .env
load_dotenv()
openai_api_key = os.getenv('OPENAI_API_KEY')
anthropic_api_key = os.getenv('ANTHROPIC_API_KEY')

# Modelos disponibles
models = {
    "openai": ["gpt-4o"],
    "anthropic": [
        "claude-3-opus-20240229",
        "claude-3-sonnet-20240229",
        "claude-3-haiku-20240307"
    ]
}

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
def analyze_image_openai(image_path, model):
    try:
        encoded_image = encode_image(image_path)
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {openai_api_key}"
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
            "model": model,
            "temperature": 0.5,
            "messages": [message],
            "max_tokens": 1000
        }
        response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
        return response.json()
    except Exception as e:
        print(f"Error analyzing image: {e}")

# Función para analizar la imagen usando la API de Anthropic
def analyze_image_anthropic(image_path, model):
    try:
        base64_string, media_type = encode_image(image_path), "image/jpeg"
        message_list = [
            {
                "role": 'user',
                "content": [
                    {"type": "image", "source": {"type": "base64", "media_type": media_type, "data": base64_string}},
                    {"type": "text", "text": "Please describe the contents of this image."}
                ]
            }
        ]
        client = Anthropic(api_key=anthropic_api_key)
        response = client.messages.create(
            model=model,
            max_tokens=2048,
            messages=message_list
        )
        return response.content[0].text if response.content and response.content[0].text else ""
    except Exception as e:
        print(f"Error during Anthropic analysis: {e}")
        return ""

# Función para convertir texto a audio usando la API de OpenAI y reproducirlo
def text_to_speech(text):
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

# Función principal para capturar y analizar la imagen, luego convertir el resultado en audio
def main(api_choice, model_choice):
    try:
        image_path = capture_screen()
        if image_path:
            if api_choice == "openai":
                response = analyze_image_openai(image_path, model_choice)
                response_text = response.get("choices")[0].get("message").get("content")
            elif api_choice == "anthropic":
                response_text = analyze_image_anthropic(image_path, model_choice)
            else:
                print("Modelo no reconocido. Use 'openai' o 'anthropic'.")
                return
            print(f"Analysis result: {response_text}")
            text_to_speech(response_text)
    except Exception as e:
        print(f"Error in main: {e}")

# Variables globales para gestionar la combinación de teclas
current_keys = set()
stop_event = threading.Event()

# Función para manejar eventos de teclado
def on_press(key):
    try:
        current_keys.add(key)
        if keyboard.Key.ctrl_l in current_keys or keyboard.Key.ctrl_r in current_keys:
            if keyboard.Key.space in current_keys:
                print("Activado.")
                main(api_choice, model_choice)
                current_keys.clear()
    except Exception as e:
        print(f"Error on_press: {e}")

def on_release(key):
    try:
        current_keys.discard(key)
    except Exception as e:
        print(f"Error on_release: {e}")

# Función para manejar la señal de interrupción y cerrar el programa de manera ordenada
def signal_handler(sig, frame):
    print('Interrupción recibida, cerrando el programa...')
    stop_event.set()
    sys.exit(0)

# Registrar el manejador de señal
signal.signal(signal.SIGINT, signal_handler)

# Escuchar eventos de teclado en un hilo separado
def start_listener():
    with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
        stop_event.wait()
        listener.stop()

# Función para seleccionar el modelo
def select_model():
    print("Seleccione el API:")
    for i, api in enumerate(models.keys(), 1):
        print(f"{i}. {api}")
    api_choice = list(models.keys())[int(input("Ingrese el número del API: ")) - 1]

    print("Seleccione el modelo:")
    for i, model in enumerate(models[api_choice], 1):
        print(f"{i}. {model}")
    model_choice = models[api_choice][int(input("Ingrese el número del modelo: ")) - 1]

    return api_choice, model_choice

# Preguntar por el modelo antes de iniciar el listener
api_choice, model_choice = select_model()

# Iniciar el listener de teclado en un hilo separado
listener_thread = threading.Thread(target=start_listener)
listener_thread.start()

print("Presiona 'Ctrl + Espacio' para activar la función.")
print("Presiona 'Ctrl + C' para detener el programa.")

# Mantener el programa en ejecución hasta que se reciba una señal de interrupción
try:
    while not stop_event.is_set():
        time.sleep(1)
except KeyboardInterrupt:
    signal_handler(signal.SIGINT, None)
