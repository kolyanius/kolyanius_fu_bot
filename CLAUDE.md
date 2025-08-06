# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Telegram bot called "Отмазочник" (Excuse Generator) that generates humorous, stylized excuses for various situations. The bot integrates with OpenRouter's LLM API to generate creative responses in different styles (быдло, корпорат, монах, инфоцыган).

## Core Architecture

**Monolithic Python Application:**
- Single process, single container deployment
- Synchronous processing with aiogram async handlers
- In-memory state + file-based configuration/logging
- Telegram polling (no webhooks)

**Key Components:**
- `app/main.py` - Entry point and application startup
- `app/bot.py` - aiogram handlers and Telegram bot logic  
- `app/llm_client.py` - OpenRouter API client with retry/fallback logic
- `app/config.py` - Configuration management with validation
- `app/prompts.py` - LLM prompts for different excuse styles

## Development Commands

**Docker Operations:**
```bash
# Start the bot (note: no hyphen in docker compose)
docker compose up

# Start with rebuild
docker compose up --build

# Stop the bot
docker compose down

# View logs
docker compose logs -f bot
```

**Testing/Validation:**
```bash
# Validate configuration
python -c "from app.config import config; print('Config OK')"

# Test module imports
python -m app.main
```

## Environment Setup

**Required Environment Variables (.env):**
```bash
TELEGRAM_BOT_TOKEN=your_bot_token_here
OPENROUTER_API_KEY=your_openrouter_key_here
LLM_BASE_URL=https://openrouter.ai/api/v1
```

**Dependencies (requirements.txt):**
- aiogram>=3.14.0 - Telegram Bot API
- openai>=1.54.0 - OpenRouter client
- python-dotenv>=1.0.0 - Environment variables
- httpx>=0.27.0 - HTTP client

## Code Conventions

**Follow KISS principles strictly:**
- No over-engineering, maximum simplicity
- Single responsibility per file
- No nested folders in app/
- PEP 8 with typing hints required
- f-strings for formatting, snake_case for functions/variables

**Error Handling Strategy:**
- All errors logged with full tracebacks
- User receives standard error messages only
- 1 retry for LLM API calls
- Graceful fallback responses when LLM fails

**Configuration Pattern:**
```python
@dataclass
class Config:
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    # ... other config
    
    def validate(self):
        if not self.TELEGRAM_BOT_TOKEN:
            raise ValueError("TELEGRAM_BOT_TOKEN is required")
```

## Project Development Status

The project follows iterative development as documented in `doc/` folder:
- **Iteration 1-2 Complete**: Basic structure + simple bot
- **Iteration 3 Complete**: LLM integration with basic prompts
- **Current**: Bot responds to any message using basic LLM prompt

**Planned Features** (see doc/vision.md):
- Style selection with inline keyboards (быдло, корпорат, монах, инфоцыган)
- Multiple prompt templates for different excuse styles
- User state management for style selection flow

## Logging Structure

**Log Files:**
- `logs/app.log` - General application events
- `logs/errors.log` - Error tracking with tracebacks  
- `logs/requests.log` - User interactions (planned)

**LLM Integration Details:**
- Model: gpt-4o (fast model for quick responses)
- Timeout: 10 seconds with asyncio.wait_for
- Fallback responses when API fails
- Special handling for rate limits

## Testing Approach

Manual testing only - no unit tests per project conventions:
1. Start bot with `docker compose up`
2. Send `/start` command
3. Test message handling and LLM responses
4. Verify error handling and fallbacks

## File Structure

```
app/
├── __init__.py
├── main.py              # Entry point
├── bot.py               # aiogram handlers  
├── llm_client.py        # OpenRouter client
├── config.py            # Configuration
├── prompts.py           # LLM prompts
└── styles.py            # Excuse styles (planned)
doc/                     # Project documentation
logs/                    # Application logs
```

## Development Workflow

The project follows a strict workflow documented in `doc/workflow.md`:
1. Read current task from tasklist
2. Propose solution and get confirmation before implementing
3. Implement according to conventions
4. Commit with descriptive messages
5. Update progress before moving to next task

Always validate configuration on startup and log all errors for debugging.