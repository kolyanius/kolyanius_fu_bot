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
        # Короткие timeout'ы для быстрого ответа
        _client = openai.OpenAI(
            base_url=config.LLM_BASE_URL,
            api_key=config.OPENROUTER_API_KEY,
            timeout=15.0,  # Короткий timeout для быстрого ответа
            max_retries=2   # Максимум 2 попытки
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
    
    # Список запасных ответов если LLM не отвечает
    fallback_responses = [
        "Понимаю вашу ситуацию. Попробую помочь с отмазкой.",
        "Хм, дайте подумать над хорошей отмазкой...",
        "Сейчас придумаю что-то подходящее!",
        "Минутку, генерирую идеальную отмазку..."
    ]
    
    try:
        # Ограничиваем общее время выполнения
        async def make_request():
            client = get_client()
            response = client.chat.completions.create(
                model=config.MODEL_NAME,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=config.MAX_TOKENS,
                temperature=config.TEMPERATURE
            )
            return response.choices[0].message.content.strip()
        
        # Ждем максимум 10 секунд
        return await asyncio.wait_for(make_request(), timeout=10.0)
        
    except asyncio.TimeoutError:
        logger.warning("LLM request timeout - using fallback")
        import random
        return random.choice(fallback_responses)
        
    except Exception as e:
        logger.error(f"LLM API error: {e}")
        # Если ошибка rate limit - даем специальный ответ
        if "rate limit" in str(e).lower() or "429" in str(e):
            return "Сейчас много запросов, попробуйте через минутку!"
        return "Произошла ошибка, попробуйте еще раз"
