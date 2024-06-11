from pynput import keyboard
import threading
import sys
import signal

current_keys = set()
stop_event = threading.Event()

# Función para manejar la señal de interrupción y cerrar el programa de manera ordenada
def signal_handler(sig, frame):
    print('Interrupción recibida, cerrando el programa...')
    stop_event.set()
    sys.exit(0)

# Registrar el manejador de señal
signal.signal(signal.SIGINT, signal_handler)

# Función para manejar eventos de teclado
def on_press(main, api_choice, model_choice, image_size, detail):
    def inner(key):
        try:
            current_keys.add(key)
            if keyboard.Key.ctrl_l in current_keys or keyboard.Key.ctrl_r in current_keys:
                if keyboard.Key.space in current_keys:
                    print("Activado.")
                    main(api_choice, model_choice, image_size, detail)
                    current_keys.clear()
        except Exception as e:
            print(f"Error on_press: {e}")
    return inner

def on_release(key):
    try:
        current_keys.discard(key)
    except Exception as e:
        print(f"Error on_release: {e}")

# Escuchar eventos de teclado en un hilo separado
def start_listener(main, api_choice, model_choice, image_size, detail):
    with keyboard.Listener(on_press=on_press(main, api_choice, model_choice, image_size, detail), on_release=on_release) as listener:
        stop_event.wait()
        listener.stop()

