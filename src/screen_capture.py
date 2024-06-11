import pyautogui
from PIL import Image
import time
import os

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
