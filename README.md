## Установка и настройка

### 1. Клонирование репозитория

```bash
git clone https://github.com/AydarGataullin7/fastapi_ai.git
cd fastspi_ai
```
### 2. Создание виртуального окружения
```bash
uv venv --python 3.12
.venv\Scripts\activate
```
### 3. Установка зависимостей
```bash
uv pip install -e .
uv pip install git+https://github.com/devmanorg/html-page-generator.git
```
### 4. Настройка переменных окружения
Скопируйте файл `example.env` в `.env`:

```bash
cp example.env .env
```
Откройте файл `.env` и заполните значения:

| Переменная | Описание | Где взять |
|------------|----------|-----------|
| `DEEPSEEK_API_KEY` | API-ключ для DeepSeek | [DeepSeek Platform](https://platform.deepseek.com/) |
| `DEEPSEEK_BASE_URL` | URL API DeepSeek (по умолчанию `https://api.deepseek.com/v1`) | Оставить по умолчанию |
| `DEEPSEEK_MODEL` | Модель DeepSeek (по умолчанию `deepseek-chat`) | Оставить по умолчанию |
| `DEEPSEEK_MAX_CONNECTIONS` | Максимальное количество подключений (по умолчанию 5) | Опционально |
| `UNSPLASH_TOKEN` | Access Key из Unsplash | [Unsplash Developers](https://unsplash.com/developers) |
| `UNSPLASH_MAX_CONNECTIONS` | Максимальное количество подключений (по умолчанию 5) | Опционально |
| `UNSPLASH_TIMEOUT` | Таймаут подключения в секундах (по умолчанию 20) | Опционально |
| `DEBUG` | Режим отладки (`True`/`False`) | Для разработки установить `True` |

### 5. Запуск сервера
```bash
fastapi dev src/main.py
```
