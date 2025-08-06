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
        logger.info(f"Initializing OpenAI client: {config.LLM_BASE_URL}")
        logger.info(f"API key length: {len(config.OPENROUTER_API_KEY)}")
        
        _client = openai.OpenAI(
            base_url=config.LLM_BASE_URL,
            api_key=config.OPENROUTER_API_KEY,
            timeout=30.0,   # Увеличиваем для отладки
            max_retries=0   # Убираем retry для чистоты
        )
    return _client


async def generate_text(prompt: str) -> str:
    """
    Генерация текста через OpenRouter с retry логикой
    
    Args:
        prompt: Промпт для генерации
        
    Returns:
        Сгенерированный текст или сообщение об ошибке
    """
    import asyncio
    
    # Простые fallback ответы
    fallback_responses = [
        "Произошла ошибка, попробуйте еще раз",
        "Сервер временно недоступен", 
        "Попробуйте повторить запрос"
    ]
    
    try:
        # Прямой синхронный вызов БЕЗ executor - проверяем основную проблему
        logger.info(f"Making LLM request to {config.LLM_BASE_URL}")
        
        client = get_client()
        response = client.chat.completions.create(
            model=config.MODEL_NAME,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=100,  # Вернули как было
            temperature=0.7  # Вернули как было
        )
        result = response.choices[0].message.content.strip()
        
        logger.info(f"LLM response successful: {len(result)} chars")
        return result
        
    except asyncio.TimeoutError:
        logger.warning("LLM request timeout")
        import random
        return random.choice(fallback_responses)
        
    except Exception as e:
        logger.error(f"LLM API error: {e}")
        import random
        return random.choice(fallback_responses)
