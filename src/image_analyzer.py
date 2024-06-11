import base64
import requests
from anthropic import Anthropic
from src.config_reader import read_config_text
from src.cost_calculator import calculate_openai_cost, calculate_anthropic_cost

# Función para codificar la imagen en base64
def encode_image(image_path):
    try:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    except Exception as e:
        print(f"Error encoding image: {e}")

# Función para analizar la imagen usando la API de OpenAI
def analyze_image_openai(image_path, model, image_size, detail, openai_api_key, total_cost_openai):
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

        return response.json(), total_cost_openai
    except Exception as e:
        print(f"Error analyzing image: {e}")

# Función para analizar la imagen usando la API de Anthropic
def analyze_image_anthropic(image_path, model, image_size, anthropic_api_key, total_cost_anthropic):
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

        return response.content[0].text if response.content and response.content[0].text else "", total_cost_anthropic
    except Exception as e:
        print(f"Error during Anthropic analysis: {e}")
        return "", total_cost_anthropic
