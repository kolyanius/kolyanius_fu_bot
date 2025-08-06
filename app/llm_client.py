"""
Клиент для работы с OpenRouter LLM API
"""
import logging
import openai
from app.config import config

logger = logging.getLogger(__name__)

# Ленивая инициализация клиента
_client = None

def get_client():
    """Получить OpenAI клиент с ленивой инициализацией"""
    global _client
    if _client is None:
        _client = openai.OpenAI(
            base_url=config.LLM_BASE_URL,
            api_key=config.OPENROUTER_API_KEY
        )
    return _client

async def generate_text(prompt: str) -> str:
    """
    Генерация текста через OpenRouter
    
    Args:
        prompt: Промпт для генерации
        
    Returns:
        Сгенерированный текст или сообщение об ошибке
    """
    try:
        client = get_client()
        response = client.chat.completions.create(
            model=config.MODEL_NAME,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=config.MAX_TOKENS,
            temperature=config.TEMPERATURE
        )
        return response.choices[0].message.content.strip()
        
    except Exception as e:
        logger.error(f"LLM API error: {e}")
        return "Произошла ошибка, попробуйте еще раз"
