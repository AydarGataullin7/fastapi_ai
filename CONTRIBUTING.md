# Разработчикам бэкенда

[TOC]

## Как развернуть локально

### Необходимое ПО

Для запуска ПО вам понадобятся консольный Git и Make. Инструкции по их установке ищите на
официальных сайтах:

- [Git SCM](https://git-scm.com/)
- [GNU Make](https://www.gnu.org/software/make/)

Вы можете проверить, установлены ли эти программы с помощью команд:
```shell
$ git --version
git version 2.37.1.windows.1

$ make --version
GNU Make 4.4.1
Built for Windows32
<...>
```

Для тех, кто использует Windows необходимы также программы **git** и **git bash**. В **git bash** необходимо дополнительно установить
**make**:

- Перейдите на сайт [ezwinports](https://sourceforge.net/projects/ezwinports/files/)
- Скачайте `make-4.4.1-without-guile-w32-bin.zip` (выберите версию без `guile`)
- Извлеките архив
- Скопируйте содержимое архива в `C:\ProgramFiles\Git\mingw64\` **БЕЗ** перезаписи/замены любых вложенных файлов.

Все дальнейшие команды запускать из-под **git bash**.

### Настройка MinIO (S3-совместимое хранилище)

Для работы приложения требуется локальное S3-хранилище. Мы используем [MinIO](https://min.io/).

#### Установка MinIO

1. Скачайте исполняемый файл MinIO Server для вашей ОС:
   - **Windows**: [minio.exe](https://dl.min.io/server/minio/release/windows-amd64/minio.exe)
   - **macOS (Intel)**: [minio](https://dl.min.io/server/minio/release/darwin-amd64/minio)
   - **macOS (Apple Silicon)**: [minio](https://dl.min.io/server/minio/release/darwin-arm64/minio)
   - **Linux**: [minio](https://dl.min.io/server/minio/release/linux-amd64/minio)

2. Поместите скачанный файл в корень проекта или удобную папку (например, `D:\minio\`).

3. Создайте папку для хранения данных MinIO:
   ```bash
   mkdir D:\minio_data
   ```

#### Запуск MinIO
Запустите сервер из терминала:
```bash
# Windows
.\minio.exe server D:\minio_data --console-address :9001
```
```bash
# macOS/Linux
./minio server ~/minio-data --console-address :9001
```
После запуска вы увидите:
```text
API: http://127.0.0.1:9000
Console: http://127.0.0.1:9001
RootUser: minioadmin
RootPass: minioadmin
```
`API`: используется приложением для загрузки файлов (`порт 9000`)

`Console`: веб-интерфейс для управления бакетами (`порт 9001`)

`Учетные данные`: `minioadmin` / `minioadmin` (по умолчанию)

#### Настройка бакета
1. Откройте веб-интерфейс:`http://127.0.0.1:9001`
2. Войдите с логином `minioadmin` и паролем `minioadmin`.
3. Нажмите `"Create Bucket"` и создайте бакет с именем `fastai`.
4. Сделайте бакет публичным через командную строку (MinIO Client):

- Скачайте MinIO Client (`mc`):
   ```bash
   # Windows
   Invoke-WebRequest -Uri "https://dl.min.io/client/mc/release/windows-amd64/mc.exe" -OutFile "mc.exe"

   # macOS/Linux
   wget https://dl.min.io/client/mc/release/linux-amd64/mc
   chmod +x mc
   ```

- Настройте алиас для подключения к MinIO:
   ```bash
   ./mc alias set myminio http://127.0.0.1:9000 minioadmin minioadmin
   ```

- Сделайте бакет `fastai` публичным:
   ```bash
   ./mc anonymous set public myminio/fastai
   ```

- Проверьте, что бакет стал публичным:
   ```bash
   ./mc anonymous get myminio/fastai
   ```
   Должно отобразиться `public`.

```env
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_BUCKET=fastai
MINIO_SECURE=False
```
#### Проверка работы
Проверьте, что `MinIO` доступен:
```bash
curl http://127.0.0.1:9000/minio/health/ready
```
Должен вернуться ответ `OK`.

#### Первая ручная загрузка файла

После настройки бакета загрузите в него тестовый файл вручную через веб-интерфейс. Это позволит:
- Убедиться, что бакет доступен и публичный
- Получить ссылку на файл для использования в эндпоинтах

1. Откройте веб-интерфейс: `http://127.0.0.1:9001`
2. Зайдите в бакет `fastai`
3. Нажмите **"Upload"** и выберите любой файл (например, `test.html`)
4. Скопируйте публичную ссылку на файл:
   ```
   http://127.0.0.1:9000/fastai/test.html
   ```
5. Откройте ссылку в браузере — файл должен открыться.

Эта ссылка понадобится при реализации эндпоинтов, возвращающих URL-адреса файлов.

#### Остановка `MinIO`
Для остановки сервера нажмите `Ctrl+C` в терминале.

### Настройка Gotenberg (генерация скриншотов)

Для генерации скриншотов сгенерированных сайтов используется публичное Demo API [Gotenberg](https://gotenberg.dev/).

#### Переменные окружения

Добавьте в `.env`:

```env
GOTENBERG_URL=https://demo.gotenberg.dev
GOTENBERG_WIDTH=1024
GOTENBERG_FORMAT=png
GOTENBERG_WAIT_DELAY=5
GOTENBERG_TIMEOUT=60
GOTENBERG_MAX_CONNECTIONS=5
```

| Переменная | Описание | Обязательная |
|------------|----------|--------------|
| `GOTENBERG_URL` | URL API Gotenberg | Да |
| `GOTENBERG_WIDTH` | Ширина скриншота в пикселях | Нет |
| `GOTENBERG_FORMAT` | Формат изображения (`png`, `jpeg`, `webp`) | Нет |
| `GOTENBERG_WAIT_DELAY` | Задержка для анимаций (сек) | Нет |
| `GOTENBERG_TIMEOUT` | Таймаут запроса (сек) | Нет |
| `GOTENBERG_MAX_CONNECTIONS` | Лимит одновременных подключений | Нет |

#### Проверка работы

Проверьте, что сервис доступен:

```bash
curl https://demo.gotenberg.dev/health
```

Должен вернуться ответ:

```json
{"status":"up","details":{"chromium":{"status":"up"},"libreoffice":{"status":"up"}}}
```

### Создание виртуального окружения для работы с IDE

IDE для корректной работы подсказок необходимо развернуть виртуальное окружение со всеми установленными зависимостями.

В качестве пакетного менеджера на проекта используется [uv](https://docs.astral.sh/uv/).

[Установите uv](https://gitlab.dvmn.org/root/fastapi-articles/-/wikis/Uv-package-manager#1-%D1%83%D1%81%D1%82%D0%B0%D0%BD%D0%BE%D0%B2%D0%BA%D0%B0-uv) и в корне репозитория выполните команду

```shell
$ uv sync
```

[uv](https://docs.astral.sh/uv/) создаст виртуальное окружение, установит необходимую версию Python и все необходимые зависимости.

После этого активируйте виртуальное окружение в текущей сессии терминала:

```shell
$ source .venv/bin/activate  # для Linux
$ .\.venv\Scripts\activate  # Для Windows
```

### Настройка pre-commit хуков

В репозитории используются хуки [pre-commit](https://pre-commit.com/), чтобы автоматически запускать линтеры и автотесты.

В корне репозитория в **активированном виртуальном окружении** запустите команду для настройки хуков:

```shell
$ pre-commit install
pre-commit installed at .git/hooks/pre-commit
```

В последующем при коммите автоматически будут запускаться линтеры и другие проверки. Если проверки не пройдут, то коммит прервётся с ошибкой.

Если вам потребуется сделать коммит без проверок, то вы можете отключить их с помощью флага `--no-verify`:
```shell
git commit -m 'Message' --no-verify
```

## Как вести разработку

Код проекта находится в папке `/src`.

Находясь в корневой директории проекта, запустить проект можно командой:

```shell
$ fastapi dev src/main.py
```

Проект будет работать по адресу http://127.0.0.1:8000/

### Как установить python-пакет в виртуальное окружение

В качестве менеджера пакетов используется [uv](https://docs.astral.sh/uv/).

Вот пример как добавить в зависимости библиотеку `beautifulsoup4`.

```shell
$ uv add beautifulsoup4
```

Конфигурационные файлы `pyproject.toml` и `uv.lock` обновятся автоматически.

Аналогичным образом можно удалять python-пакеты:

```shell
$ uv remove beautifulsoup4
```

Если необходимо обновить `uv.lock` вручную, то используйте команду:

```shell
$ uv lock
```

## Архитектура проекта

Схемы, описывающие структуру приложения:
- [Схема локальной инсталляции бэкенда](https://gitlab.dvmn.org/root/fastapi-articles/-/wikis/fastai/backend_local_installation.drawio.png)
- [Схема продовой инсталляции бэкенда](https://gitlab.dvmn.org/root/fastapi-articles/-/wikis/fastai/backend_prod_installation.drawio.png)
- [Схема декомпозиции бэкенда по подсистемам](https://gitlab.dvmn.org/root/fastapi-articles/-/wikis/fastai/backend_decomposition.drawio.png)

## Инструменты разработки

### Проверка и форматирование кода

В проекте используется [Ruff](https://docs.astral.sh/ruff/) для линтинга и форматирования кода.

**Проверить код на ошибки:**
```shell
$ make lint
```
`Ruff` проверит код в папке `src/` и покажет все нарушения стиля, ошибки импортов и другие проблемы.

Автоматически исправить ошибки:

```shell
$ make format
```
`Ruff` попытается автоматически исправить найденные проблемы (форматирование, порядок импортов).

### Pre-commit хуки
Хуки уже настроены в файле `.pre-commit-config.yaml`. Они автоматически запускают `ruff` и `editorconfig-checker` перед каждым коммитом.

Если вы хотите проверить, как работают хуки, выполните:

```shell
$ pre-commit run --all-files
```
### Работа с коммитами
1. Успешный коммит (все проверки пройдены)
Если вы внесли изменения и все проверки прошли, коммит создастся успешно:

```shell
$ git add .
$ git commit -m "Описание изменений"
```
2. Коммит с ошибками линтера

Если `Ruff` находит ошибки, коммит прервётся. Вы увидите сообщение с указанием файла, строки и типа ошибки. Исправьте ошибки и повторите коммит.

3. Быстрый коммит (пропуск проверок)
Для правок документации или других срочных изменений можно пропустить хуки:

```shell
$ git commit -m "Описание изменений" --no-verify
```
4. Файл `.env`
Файл `.env` с переменными окружения добавлен в `.gitignore` и не должен попадать в репозиторий. Это защищает секретные данные (ключи API, пароли) от случайной публикации.

### Команды для быстрого запуска с помощью make

Для вывода списка часто используемых коротких команд используйте команду

```shell
$ make list
...
```
