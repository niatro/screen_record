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

# Costos acumulativos
total_cost_openai = 0
total_cost_anthropic = 0

# Asegurar que las carpetas 'images', 'audio' y 'config' existen
if not os.path.exists('images'):
    os.makedirs('images')
if not os.path.exists('audio'):
    os.makedirs('audio')
if not os.path.exists('config'):
    os.makedirs('config')

# Función para leer el texto desde el archivo de configuración
def read_config_text():
    config_file_path = os.path.join('config', 'config_text.txt')
    if not os.path.exists(config_file_path):
        with open(config_file_path, 'w') as file:
            file.write("Texto de configuración predeterminado")
    with open(config_file_path, 'r') as file:
        return file.read()

# Función para capturar la pantalla, redimensionar y guardar la imagen
def capture_screen(image_size):
    try:
        screenshot = pyautogui.screenshot()
        resized_screenshot = screenshot.resize(image_size, Image.LANCZOS)
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

# Función para calcular el costo de procesamiento para OpenAI
def calculate_openai_cost(image_size, detail):
    if detail == "low":
        return 85
    elif detail == "high":
        width, height = image_size
        short_side = min(width, height)
        num_tiles = (short_side // 512) * (max(width, height) // 512)
        return 85 + (num_tiles * 170)
    return 0

# Función para analizar la imagen usando la API de OpenAI
def analyze_image_openai(image_path, model, image_size, detail):
    global total_cost_openai
    try:
        config_text = read_config_text()
        encoded_image = encode_image(image_path)
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {openai_api_key}"
        }
        message = {
            "role": "user",
            "content": [
                {"type": "text", "text": config_text},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpg;base64,{encoded_image}",
                        "detail": detail
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
        
        # Calcular el costo y agregar al costo acumulativo
        cost = calculate_openai_cost(image_size, detail)
        total_cost_openai += cost
        print(f"OpenAI Cost: {cost} tokens, Total OpenAI Cost: {total_cost_openai} tokens")

        return response.json()
    except Exception as e:
        print(f"Error analyzing image: {e}")

# Función para calcular el costo de procesamiento para Anthropic
def calculate_anthropic_cost(image_size):
    width, height = image_size
    if width > 1568 or height > 1568:
        return 1600  # Approximate cost in tokens for large images
    return 1600  # Approximate cost in tokens for optimal size images

# Función para analizar la imagen usando la API de Anthropic
def analyze_image_anthropic(image_path, model, image_size):
    global total_cost_anthropic
    try:
        config_text = read_config_text()
        base64_string, media_type = encode_image(image_path), "image/jpeg"
        message_list = [
            {
                "role": 'user',
                "content": [
                    {"type": "image", "source": {"type": "base64", "media_type": media_type, "data": base64_string}},
                    {"type": "text", "text": config_text}
                ]
            }
        ]
        client = Anthropic(api_key=anthropic_api_key)
        response = client.messages.create(
            model=model,
            max_tokens=2048,
            messages=message_list
        )
        
        # Calcular el costo y agregar al costo acumulativo
        cost = calculate_anthropic_cost(image_size)
        total_cost_anthropic += cost
        print(f"Anthropic Cost: {cost} tokens, Total Anthropic Cost: {total_cost_anthropic} tokens")

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
def main(api_choice, model_choice, image_size, detail=None):
    try:
        image_path = capture_screen(image_size)
        if image_path:
            if api_choice == "openai":
                response = analyze_image_openai(image_path, model_choice, image_size, detail)
                response_text = response.get("choices")[0].get("message").get("content")
            elif api_choice == "anthropic":
                response_text = analyze_image_anthropic(image_path, model_choice, image_size)
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
                main(api_choice, model_choice, image_size, detail)
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

# Función para seleccionar el modelo y el tamaño de la imagen
def select_model_and_size():
    print("Seleccione el API:")
    for i, api in enumerate(models.keys(), 1):
        print(f"{i}. {api}")
    api_choice = list(models.keys())[int(input("Ingrese el número del API: ")) - 1]

    print("Seleccione el modelo:")
    for i, model in enumerate(models[api_choice], 1):
        print(f"{i}. {model}")
    model_choice = models[api_choice][int(input("Ingrese el número del modelo: ")) - 1]

    print("Seleccione el tamaño de la imagen:")
    print("1. 512x512")
    print("2. 1024x1024")
    image_size_choice = int(input("Ingrese el número del tamaño de la imagen: "))
    image_size = (512, 512) if image_size_choice == 1 else (1024, 1024)

    detail = None
    if api_choice == "openai":
        print("Seleccione el nivel de detalle:")
        print("1. low")
        print("2. high")
        detail_choice = int(input("Ingrese el número del nivel de detalle: "))
        detail = "low" if detail_choice == 1 else "high"

    return api_choice, model_choice, image_size, detail

# Preguntar por el modelo y tamaño de la imagen antes de iniciar el listener
api_choice, model_choice, image_size, detail = select_model_and_size()

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
