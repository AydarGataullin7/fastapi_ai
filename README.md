# FastAI — ИИ-генератор сайтов

## Требования
- `Python 3.13`
- `Git`
- `Make`
- `UV`

## Установка и запуск

1. Клонируйте репозиторий:
   ```bash
   git clone https://github.com/AydarGataullin7/fastapi_ai.git
   cd fastapi_ai
   ```
Создайте виртуальное окружение и установите зависимости:

```bash
uv sync
```
Активируйте виртуальное окружение:

```bash
.\.venv\Scripts\activate   # Windows
source .venv/bin/activate   # Linux/Mac
```
Запустите приложение:

```bash
fastapi dev src/main.py
```
Откройте в браузере: `http://127.0.0.1:8000/docs`
