#!/usr/bin/env python3
"""
Тест LLM провайдера для диагностики проблем
"""
import os
import sys
import asyncio
from dotenv import load_dotenv
import openai

# Загружаем переменные окружения
load_dotenv()

def test_environment():
    """Проверка переменных окружения"""
    print("Проверка переменных окружения:")
    
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    api_key = os.getenv("OPENROUTER_API_KEY") 
    base_url = os.getenv("LLM_BASE_URL", "https://gptunnel.ru/v1")
    
    print(f"TELEGRAM_BOT_TOKEN: {'OK Установлен' if bot_token else 'FAIL Отсутствует'}")
    print(f"OPENROUTER_API_KEY: {'OK Установлен' if api_key else 'FAIL Отсутствует'} (длина: {len(api_key) if api_key else 0})")
    print(f"LLM_BASE_URL: {base_url}")
    
    if not api_key:
        print("ОШИБКА: OPENROUTER_API_KEY не найден в .env файле")
        return False
        
    return True

def test_openai_client():
    """Тест создания OpenAI клиента"""
    print("\nТест создания OpenAI клиента:")
    
    try:
        api_key = os.getenv("OPENROUTER_API_KEY")
        base_url = os.getenv("LLM_BASE_URL", "https://gptunnel.ru/v1")
        
        client = openai.OpenAI(
            api_key=api_key,
            base_url=base_url,
            timeout=30.0
        )
        print("OK OpenAI клиент создан успешно")
        return client
        
    except Exception as e:
        print(f"FAIL Ошибка создания клиента: {e}")
        return None

def test_sync_request(client):
    """Тест синхронного запроса"""
    print("\nТест синхронного запроса:")
    
    if not client:
        print("FAIL Клиент не создан, пропускаем тест")
        return
        
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": "Скажи 'Привет' одним словом"}],
            max_tokens=10,
            temperature=0.1
        )
        
        result = response.choices[0].message.content.strip()
        print(f"OK Синхронный запрос успешен: '{result}'")
        return True
        
    except Exception as e:
        print(f"FAIL Ошибка синхронного запроса: {e}")
        print(f"   Тип ошибки: {type(e).__name__}")
        return False

async def test_async_request():
    """Тест асинхронного запроса через app.llm_client"""
    print("\nТест асинхронного запроса через app.llm_client:")
    
    try:
        # Импортируем модуль приложения
        sys.path.append('.')
        from app.llm_client import generate_text
        
        result = await generate_text("Скажи 'Тест' одним словом")
        print(f"OK Асинхронный запрос успешен: '{result}'")
        return True
        
    except Exception as e:
        print(f"FAIL Ошибка асинхронного запроса: {e}")
        print(f"   Тип ошибки: {type(e).__name__}")
        return False

def test_config_validation():
    """Тест валидации конфигурации"""
    print("\nТест валидации конфигурации:")
    
    try:
        from app.config import config
        config.validate()
        print("OK Конфигурация валидна")
        print(f"   MODEL_NAME: {config.MODEL_NAME}")
        print(f"   MAX_TOKENS: {config.MAX_TOKENS}")
        print(f"   TEMPERATURE: {config.TEMPERATURE}")
        return True
        
    except Exception as e:
        print(f"FAIL Ошибка валидации конфигурации: {e}")
        return False

async def main():
    """Основная функция тестирования"""
    print("ДИАГНОСТИКА LLM ПРОВАЙДЕРА")
    print("=" * 40)
    
    # Тест 1: Переменные окружения
    if not test_environment():
        print("\nКРИТИЧЕСКАЯ ОШИБКА: Проверьте .env файл")
        return
    
    # Тест 2: Валидация конфигурации
    if not test_config_validation():
        print("\nКРИТИЧЕСКАЯ ОШИБКА: Проблема с конфигурацией")
        return
    
    # Тест 3: Создание клиента
    client = test_openai_client()
    
    # Тест 4: Синхронный запрос
    sync_ok = test_sync_request(client)
    
    # Тест 5: Асинхронный запрос
    async_ok = await test_async_request()
    
    # Итоги
    print("\n" + "=" * 40)
    print("ИТОГИ ДИАГНОСТИКИ:")
    print(f"Синхронный запрос: {'OK' if sync_ok else 'FAIL'}")
    print(f"Асинхронный запрос: {'OK' if async_ok else 'FAIL'}")
    
    if sync_ok and async_ok:
        print("\nВСЕ ТЕСТЫ ПРОШЛИ! LLM провайдер работает корректно")
    else:
        print("\nОБНАРУЖЕНЫ ПРОБЛЕМЫ! Проверьте:")
        print("   1. Правильность API ключа в .env")
        print("   2. Доступность gptunnel.ru")
        print("   3. Баланс на аккаунте")
        print("   4. Корректность модели gpt-4o")

if __name__ == "__main__":
    asyncio.run(main())