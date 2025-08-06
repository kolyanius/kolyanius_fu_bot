"""
Стили отмазок для бота "Отмазочник"
"""

STYLES = {
    "быдло": {
        "name": "Быдло",
        "emoji": "💪",
        "description": "Грубоватые, прямолинейные отмазки с жаргоном"
    }
}

def get_style_info(style_key: str) -> dict:
    """Получить информацию о стиле"""
    return STYLES.get(style_key, {})

def get_available_styles() -> list:
    """Получить список доступных стилей"""
    return list(STYLES.keys())