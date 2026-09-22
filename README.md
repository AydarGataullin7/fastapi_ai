# FastAPI AI — генератор сайтов

Веб-приложение на FastAPI, которое генерирует готовые HTML-сайты по текстовому описанию (промпту) с помощью нейросети DeepSeek.

## Что делает проект

Пользователь отправляет текстовый промпт (например, «Сайт про школу программирования на Python»), и приложение:

1. **Генерирует название** сайта через DeepSeek
2. **Подбирает изображения** через Unsplash по ключевым словам из промпта
3. **Создаёт полный HTML+CSS+JS** сайта с анимациями и стилем
4. **Загружает готовый сайт** в S3-совместимое хранилище (MinIO)
5. **Делает скриншот** сгенерированного сайта через Gotenberg
6. **Возвращает ссылки** на просмотр, скачивание и превью сайта

## Какие сервисы использует

| Сервис | Назначение |
|--------|------------|
| [DeepSeek](https://platform.deepseek.com/) | Генерация названия и HTML-кода сайта |
| [Unsplash](https://unsplash.com/developers) | Поиск изображений по теме промпта |
| [MinIO](https://min.io/) | S3-совместимое хранилище для HTML и скриншотов |
| [Gotenberg](https://gotenberg.dev/) | Генерация скриншотов из HTML |

## Как это работает

```
Пользователь → POST /generate → DeepSeek → Unsplash → HTML
                                     ↓
                              MinIO ← HTML + скриншот ← Gotenberg
                                     ↓
                            Ссылки для просмотра и скачивания
```

## Технологии

- **FastAPI** — веб-фреймворк
- **DeepSeek** — языковая модель для генерации кода
- **aioboto3** — асинхронный клиент для S3
- **Gotenberg API** — генерация скриншотов
- **Pydantic Settings** — валидация настроек
- **uv** — менеджер пакетов

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
| **DeepSeek** | | |
| `DEEPSEEK_API_KEY` | API-ключ для DeepSeek | [DeepSeek Platform](https://platform.deepseek.com/) |
| `DEEPSEEK_BASE_URL` | URL API DeepSeek (по умолчанию `https://api.deepseek.com/v1`) | Оставить по умолчанию |
| `DEEPSEEK_MODEL` | Модель DeepSeek (по умолчанию `deepseek-chat`) | Оставить по умолчанию |
| `DEEPSEEK_MAX_CONNECTIONS` | Максимальное количество подключений (по умолчанию 5) | Опционально |
| **Unsplash** | | |
| `UNSPLASH_TOKEN` | Access Key из Unsplash | [Unsplash Developers](https://unsplash.com/developers) |
| `UNSPLASH_MAX_CONNECTIONS` | Максимальное количество подключений (по умолчанию 5) | Опционально |
| `UNSPLASH_TIMEOUT` | Таймаут подключения в секундах (по умолчанию 20) | Опционально |
| **S3 (MinIO)** | | |
| `MINIO_ENDPOINT` | Адрес MinIO API (по умолчанию `localhost:9000`) | Оставить для локальной разработки |
| `MINIO_ACCESS_KEY` | Логин для доступа к MinIO | `minioadmin` (по умолчанию) |
| `MINIO_SECRET_KEY` | Пароль для доступа к MinIO | `minioadmin` (по умолчанию) |
| `MINIO_BUCKET` | Имя бакета в MinIO (по умолчанию `fastai`) | Создать в веб-интерфейсе MinIO |
| `MINIO_SECURE` | Использовать HTTPS (`True`/`False`) | `False` для локальной разработки |
| `MINIO_CONNECT_TIMEOUT` | Таймаут подключения в секундах (по умолчанию 5) | Опционально |
| `MINIO_READ_TIMEOUT` | Таймаут чтения в секундах (по умолчанию 30) | Опционально |
| `MINIO_MAX_CONNECTIONS` | Лимит одновременных подключений (по умолчанию 10) | Опционально |
| **Общие** | | |
| `DEBUG` | Режим отладки (`True`/`False`) | Для разработки установить `True` |

### 5. Запуск сервера
```bash
fastapi dev src/main.py
```

### 6. Настройка MinIO (S3-хранилище)

Для работы приложения требуется локальное S3-хранилище. Подробная инструкция по установке и настройке MinIO описана в [CONTRIBUTING.md](CONTRIBUTING.md#настройка-minio-s3-совместимое-хранилище).

Кратко:

1. Скачайте MinIO Server с [официального сайта](https://min.io/)
2. Запустите сервер:
   ```bash
   ./minio server ~/minio-data --console-address :9001
   ```
3. Создайте бакет `fastai` и сделайте его публичным через веб-интерфейс `http://127.0.0.1:9001`

После настройки MinIO добавьте переменные в `.env` (см. таблицу выше).
