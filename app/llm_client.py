"""
Клиент для работы с OpenRouter LLM API
"""
import asyncio
import logging
import time
import openai
from app.config import config

logger = logging.getLogger(__name__)
error_logger = logging.getLogger("error")
request_logger = logging.getLogger("requests")

# Ленивая инициализация клиентов
_llm_client = None
_whisper_client = None

def get_client():
    """Получить OpenAI клиент для LLM с ленивой инициализацией"""
    global _llm_client
    if _llm_client is None:
        logger.info(f"Initializing LLM client: {config.LLM_BASE_URL}")
        logger.info(f"LLM API key length: {len(config.OPENROUTER_API_KEY)}")

        _llm_client = openai.OpenAI(
            base_url=config.LLM_BASE_URL,
            api_key=config.OPENROUTER_API_KEY,
            timeout=15.0,   # Разумный timeout
            max_retries=0   # Собственная retry логика
        )
    return _llm_client


def get_whisper_client():
    """Получить OpenAI клиент для Whisper API с ленивой инициализацией"""
    global _whisper_client
    if _whisper_client is None:
        logger.info(f"Initializing Whisper client: {config.WHISPER_BASE_URL}")
        logger.info(f"Whisper API key length: {len(config.WHISPER_API_KEY)}")

        _whisper_client = openai.OpenAI(
            base_url=config.WHISPER_BASE_URL,
            api_key=config.WHISPER_API_KEY,
            timeout=30.0,   # Whisper может быть медленнее
            max_retries=1
        )
    return _whisper_client


async def generate_text(prompt: str, user_id: int = None, style: str = "unknown") -> str:
    """
    Генерация текста через OpenRouter с retry логикой и логированием
    
    Args:
        prompt: Промпт для генерации
        user_id: ID пользователя для логирования
        style: Выбранный стиль для статистики
        
    Returns:
        Сгенерированный текст или fallback сообщение
    """
    start_time = time.time()
    
    # Fallback ответы для разных ошибок
    fallback_responses = {
        "timeout": [
            "Сервер медленно отвечает, попробуйте еще раз",
            "Запрос занимает слишком много времени",
            "Timeout ошибка, повторите запрос"
        ],
        "api_error": [
            "Произошла ошибка API, попробуйте позже", 
            "Сервис временно недоступен",
            "Техническая ошибка, повторите попытку"
        ],
        "rate_limit": [
            "Слишком много запросов, подождите минуту",
            "Превышен лимит запросов, попробуйте позже"
        ]
    }
    
    # Попытки с экспоненциальной задержкой
    max_retries = config.RETRY_COUNT + 1  # +1 к конфигурации
    for attempt in range(max_retries):
        try:
            if attempt > 0:
                # Экспоненциальная задержка: 1s, 2s, 4s
                delay = 2 ** (attempt - 1)
                logger.info(f"Retry {attempt}/{max_retries-1}, waiting {delay}s")
                await asyncio.sleep(delay)
            
            logger.info(f"LLM request attempt {attempt+1}/{max_retries} to {config.LLM_BASE_URL}")
            
            # Выполняем запрос в executor
            def make_request():
                client = get_client()
                return client.chat.completions.create(
                    model=config.MODEL_NAME,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=config.MAX_TOKENS,
                    temperature=config.TEMPERATURE
                )
            
            # Ждем с таймаутом
            response = await asyncio.wait_for(
                asyncio.get_event_loop().run_in_executor(None, make_request),
                timeout=15.0
            )
            
            result = response.choices[0].message.content.strip()
            elapsed_time = time.time() - start_time
            
            # Логируем успешный запрос
            request_logger.info(
                f"SUCCESS | User: {user_id} | Style: {style} | "
                f"Time: {elapsed_time:.2f}s | Length: {len(result)} | "
                f"Attempts: {attempt+1}"
            )
            
            logger.info(f"LLM response successful: {len(result)} chars in {elapsed_time:.2f}s")
            return result
            
        except asyncio.TimeoutError:
            elapsed_time = time.time() - start_time
            logger.warning(f"LLM request timeout after {elapsed_time:.2f}s (attempt {attempt+1})")
            
            if attempt == max_retries - 1:  # Последняя попытка
                error_logger.error(f"TIMEOUT | User: {user_id} | Style: {style} | Total time: {elapsed_time:.2f}s")
                import random
                return random.choice(fallback_responses["timeout"])
                
        except Exception as e:
            elapsed_time = time.time() - start_time
            error_str = str(e).lower()
            
            # Определяем тип ошибки
            if "rate limit" in error_str or "429" in error_str:
                error_logger.error(f"RATE_LIMIT | User: {user_id} | Error: {e}")
                import random
                return random.choice(fallback_responses["rate_limit"])
            
            logger.error(f"LLM API error (attempt {attempt+1}): {e}")
            
            if attempt == max_retries - 1:  # Последняя попытка
                error_logger.error(f"API_ERROR | User: {user_id} | Style: {style} | Error: {e}", exc_info=True)
                import random
                return random.choice(fallback_responses["api_error"])
    
    # Не должно сюда дойти, но на всякий случай
    import random
    return random.choice(fallback_responses["api_error"])
