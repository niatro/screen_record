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

# Función para calcular el costo de procesamiento para Anthropic
def calculate_anthropic_cost(image_size):
    width, height = image_size
    if width > 1568 or height > 1568:
        return 1600  # Approximate cost in tokens for large images
    return 1600  # Approximate cost in tokens for optimal size images
