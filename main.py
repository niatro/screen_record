import os
import time
import threading
from dotenv import load_dotenv
from pynput import keyboard
from src.screen_capture import capture_screen
from src.image_analyzer import analyze_image_openai, analyze_image_anthropic
from src.text_to_speech import text_to_speech
from src.cost_calculator import calculate_openai_cost, calculate_anthropic_cost
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

# Variables globales para gestionar la combinación de teclas
current_keys = set()
stop_event = threading.Event()

# Función para manejar la señal de interrupción y cerrar el programa de manera ordenada
def signal_handler(sig, frame):
    print('Interrupción recibida, cerrando el programa...')
    stop_event.set()
    sys.exit(0)

# Registrar el manejador de señal
signal.signal(signal.SIGINT, signal_handler)

# Función principal para capturar y analizar la imagen, luego convertir el resultado en audio
def main(api_choice, model_choice, image_size, detail=None):
    global total_cost_openai, total_cost_anthropic
    try:
        image_path = capture_screen(image_size)
        if image_path:
            if api_choice == "openai":
                response, total_cost_openai = analyze_image_openai(image_path, model_choice, image_size, detail, openai_api_key, total_cost_openai)
                response_text = response.get("choices")[0].get("message").get("content")
            elif api_choice == "anthropic":
                response_text, total_cost_anthropic = analyze_image_anthropic(image_path, model_choice, image_size, anthropic_api_key, total_cost_anthropic)
            else:
                print("Modelo no reconocido. Use 'openai' o 'anthropic'.")
                return
            print(f"Analysis result: {response_text}")
            text_to_speech(response_text, openai_api_key)
    except Exception as e:
        print(f"Error in main: {e}")

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

