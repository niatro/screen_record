import os

def read_config_text():
    config_file_path = os.path.join('config', 'config_text.txt')
    if not os.path.exists(config_file_path):
        with open(config_file_path, 'w') as file:
            file.write("Texto de configuración predeterminado")
    with open(config_file_path, 'r') as file:
        return file.read()
