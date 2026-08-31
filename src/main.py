import asyncio
import os
from datetime import datetime

from fastapi import FastAPI
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field


class UserProfileResponse(BaseModel):
    profileId: int = Field(description="Уникальный идентификатор пользователя")
    email: str = Field(description="Email пользователя")
    username: str = Field(min_length=3, max_length=20, description="Имя пользователя")
    registeredAt: str = Field(description="Дата регистрации")
    updatedAt: str = Field(description="Дата последнего обновления профиля")
    isActive: bool = Field(description="Активен ли пользователь")


class CreateSiteRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=100, description="Заголовок сайта")
    prompt: str = Field(..., min_length=1, description="Промт для генерации сайта")


class CreateSiteResponse(BaseModel):
    id: int = Field(description="Уникальный идентификатор сайта в системе")
    title: str = Field(description="Заголовок сайта")
    prompt: str = Field(description="Промт, использованный для генерации сайта")
    created_at: datetime = Field(description="Дата и время создания сайта")
    updated_at: datetime = Field(description="Дата и время последнего обновления сайта")
    view_url: str = Field(description="Ссылка для просмотра сайта в браузере")
    download_url: str = Field(description="Ссылка для скачивания HTML-файла сайта")
    screenshot_url: str = Field(description="Ссылка на скриншот сгенерированного сайта")


class GenerateSiteRequest(BaseModel):
    prompt: str = Field(..., min_length=1, description="Промпт для генерации сайта")


# HTML-заглушка из файла (скопирована с https://dvmn.org/.../index.html)
STEGOSAURUS_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Стегозавры: Гиганты Юрского периода</title>
    <link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@400;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --primary-color: #2c786c;
            --secondary-color: #f8b400;
            --accent-color: #004445;
            --text-color: #333;
            --light-bg: #f9f9f9;
            --dark-bg: #1a1a2e;
            --parallax-speed: 0.5;
        }

        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Montserrat', sans-serif;
            color: var(--text-color);
            line-height: 1.6;
            overflow-x: hidden;
            background-color: var(--light-bg);
        }

        .parallax {
            position: relative;
            height: 100vh;
            overflow: hidden;
            display: flex;
            justify-content: center;
            align-items: center;
            text-align: center;
        }

        .parallax::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: linear-gradient(rgba(0, 0, 0, 0.3), rgba(0, 0, 0, 0.7)),
                        url('https://images.unsplash.com/photo-1609398239679-45fde0d8ceee') center/cover no-repeat fixed;
            z-index: -1;
            transform: translateZ(0);
            will-change: transform;
        }

        .header-content {
            max-width: 800px;
            padding: 2rem;
            animation: fadeInUp 1.5s ease-out;
        }

        h1 {
            font-size: clamp(2.5rem, 5vw, 4rem);
            color: white;
            margin-bottom: 1rem;
            text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.5);
        }

        .subtitle {
            font-size: 1.5rem;
            color: var(--secondary-color);
            margin-bottom: 2rem;
            text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.5);
        }

        .scroll-down {
            position: absolute;
            bottom: 30px;
            left: 50%;
            transform: translateX(-50%);
            color: white;
            font-size: 1.2rem;
            animation: bounce 2s infinite;
        }

        .main-content {
            padding: 4rem 2rem;
            max-width: 1200px;
            margin: 0 auto;
        }

        section {
            margin-bottom: 3rem;
            opacity: 0;
            transform: translateY(20px);
            transition: all 0.8s ease-out;
        }

        section.visible {
            opacity: 1;
            transform: translateY(0);
        }

        h2 {
            font-size: 2.2rem;
            color: var(--primary-color);
            margin-bottom: 1.5rem;
            position: relative;
            display: inline-block;
        }

        h2::after {
            content: '';
            position: absolute;
            bottom: -10px;
            left: 0;
            width: 60px;
            height: 4px;
            background-color: var(--secondary-color);
        }

        p {
            margin-bottom: 1.5rem;
            font-size: 1.1rem;
        }

        .species-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
            gap: 2rem;
            margin-top: 2rem;
        }

        .species-card {
            background: white;
            border-radius: 10px;
            overflow: hidden;
            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.1);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }

        .species-card:hover {
            transform: translateY(-10px);
            box-shadow: 0 15px 30px rgba(0, 0, 0, 0.2);
        }

        .species-img {
            height: 200px;
            overflow: hidden;
        }

        .species-img img {
            width: 100%;
            height: 100%;
            object-fit: cover;
            transition: transform 0.5s ease;
        }

        .species-card:hover .species-img img {
            transform: scale(1.1);
        }

        .species-info {
            padding: 1.5rem;
        }

        .species-info h3 {
            color: var(--accent-color);
            margin-bottom: 0.5rem;
        }

        .species-info p {
            font-size: 0.9rem;
            color: #666;
        }

        .timeline {
            position: relative;
            max-width: 800px;
            margin: 3rem auto;
        }

        .timeline::before {
            content: '';
            position: absolute;
            top: 0;
            left: 50%;
            width: 4px;
            height: 100%;
            background: var(--secondary-color);
            transform: translateX(-50%);
        }

        .timeline-item {
            padding: 1.5rem;
            position: relative;
            width: 50%;
            margin-bottom: 2rem;
            opacity: 0;
            transform: translateX(-20px);
            transition: all 0.8s ease-out;
        }

        .timeline-item.visible {
            opacity: 1;
            transform: translateX(0);
        }

        .timeline-item:nth-child(odd) {
            left: 0;
        }

        .timeline-item:nth-child(even) {
            left: 50%;
        }

        .timeline-content {
            padding: 1.5rem;
            background: white;
            border-radius: 8px;
            box-shadow: 0 3px 10px rgba(0, 0, 0, 0.1);
        }

        .timeline-date {
            font-weight: bold;
            color: var(--primary-color);
            margin-bottom: 0.5rem;
        }

        footer {
            background-color: var(--dark-bg);
            color: white;
            text-align: center;
            padding: 2rem;
            margin-top: 3rem;
        }

        @keyframes fadeInUp {
            from {
                opacity: 0;
                transform: translateY(50px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        @keyframes bounce {
            0%, 20%, 50%, 80%, 100% {
                transform: translateY(0) translateX(-50%);
            }
            40% {
                transform: translateY(-20px) translateX(-50%);
            }
            60% {
                transform: translateY(-10px) translateX(-50%);
            }
        }

        @media (max-width: 768px) {
            .timeline::before {
                left: 30px;
            }

            .timeline-item {
                width: 100%;
                padding-left: 70px;
                padding-right: 20px;
            }

            .timeline-item:nth-child(even) {
                left: 0;
            }
        }
    </style>
</head>
<body>
    <div class="parallax">
        <div class="header-content">
            <h1>Стегозавры</h1>
            <div class="subtitle">Величественные гиганты Юрского периода</div>
        </div>
        <div class="scroll-down">↓ Прокрутите вниз ↓</div>
    </div>

    <main class="main-content">
        <section id="era">
            <h2>Эпоха стегозавров</h2>
            <p>Стегозавры населяли нашу планету в позднем Юрском периоде, примерно 155-150 миллионов лет назад. Эти удивительные существа были современниками таких известных динозавров, как аллозавры и диплодоки.</p>
            <p>Их окаменелости в основном находят в Северной Америке, хотя некоторые находки свидетельствуют о более широком распространении этих животных.</p>

            <div class="timeline">
                <div class="timeline-item">
                    <div class="timeline-content">
                        <div class="timeline-date">~155 млн лет назад</div>
                        <p>Появление первых стегозавров</p>
                    </div>
                </div>
                <div class="timeline-item">
                    <div class="timeline-content">
                        <div class="timeline-date">~150 млн лет назад</div>
                        <p>Расцвет вида Stegosaurus stenops</p>
                    </div>
                </div>
                <div class="timeline-item">
                    <div class="timeline-content">
                        <div class="timeline-date">~145 млн лет назад</div>
                        <p>Исчезновение стегозавров</p>
                    </div>
                </div>
            </div>
        </section>

        <section id="diet">
            <h2>Питание и образ жизни</h2>
            <p>Стегозавры были исключительно травоядными животными. Их рацион состоял из низкорослых растений, которые они могли достать благодаря своему небольшому росту (около 4 метров в высоту).</p>
            <p>Особенности строения зубов и челюстей указывают на то, что они питались мягкой растительностью: папоротниками, хвощами, саговниками и возможно, молодыми побегами деревьев.</p>
        </section>

        <section id="species">
            <h2>Известные виды</h2>
            <p>Палеонтологи выделяют несколько видов стегозавров, отличающихся размерами, формой пластин и шипов:</p>

            <div class="species-grid">
                <div class="species-card">
                    <div class="species-img">
                        <img src="https://images.unsplash.com/photo-1729207512292-da69be60b05a" alt="Stegosaurus stenops">
                    </div>
                    <div class="species-info">
                        <h3>Stegosaurus stenops</h3>
                        <p>Самый изученный вид с крупными пластинами и короткими шипами на хвосте. Достигал 9 метров в длину.</p>
                    </div>
                </div>

                <div class="species-card">
                    <div class="species-img">
                        <img src="https://images.unsplash.com/photo-1606108631580-78be7884b0f8" alt="Stegosaurus ungulatus">
                    </div>
                    <div class="species-info">
                        <h3>Stegosaurus ungulatus</h3>
                        <p>Отличался более узкими пластинами и длинными шипами. Некоторые особи достигали 7 метров в длину.</p>
                    </div>
                </div>

                <div class="species-card">
                    <div class="species-img">
                        <img src="https://images.unsplash.com/photo-1728848448483-2f6d1bfef9d5" alt="Stegosaurus sulcatus">
                    </div>
                    <div class="species-info">
                        <h3>Stegosaurus sulcatus</h3>
                        <p>Характеризовался глубокими бороздами на пластинах. Менее распространенный вид.</p>
                    </div>
                </div>
            </div>
        </section>
    </main>

    <footer>
        <p>© 2023 Сайт о стегозаврах | Все права защищены</p>
    </footer>

    <script>
        // Параллакс эффект
        document.addEventListener('DOMContentLoaded', () => {
            const parallax = document.querySelector('.parallax');

            window.addEventListener('scroll', () => {
                const scrollPosition = window.pageYOffset;
                parallax.style.backgroundPositionY = scrollPosition * 0.5 + 'px';
            });

            // Анимация появления секций при скролле
            const sections = document.querySelectorAll('section');
            const timelineItems = document.querySelectorAll('.timeline-item');

            const checkVisibility = () => {
                sections.forEach(section => {
                    const sectionTop = section.getBoundingClientRect().top;
                    if (sectionTop < window.innerHeight - 100) {
                        section.classList.add('visible');
                    }
                });

                timelineItems.forEach(item => {
                    const itemTop = item.getBoundingClientRect().top;
                    if (itemTop < window.innerHeight - 100) {
                        item.classList.add('visible');
                    }
                });
            };

            window.addEventListener('scroll', checkVisibility);
            checkVisibility(); // Проверить при загрузке
        });
    </script>
</body>
</html>"""


async def generate_html_stream():
    lines = STEGOSAURUS_HTML.split('\n')
    for line in lines:
        yield line + '\n'
        await asyncio.sleep(0.2)


app = FastAPI()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")

app.mount("/assets", StaticFiles(directory=os.path.join(FRONTEND_DIR, "assets")), name="assets")


@app.get("/")
def serve_index():
    return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))


@app.get("/frontend-settings.json")
def serve_settings():
    return FileResponse(os.path.join(FRONTEND_DIR, "frontend-settings.json"))


@app.get("/frontend-api/users/me", response_model=UserProfileResponse)
def get_current_user():
    return {
        "profileId": 1,
        "email": "mock@user.com",
        "username": "mock-user",
        "registeredAt": "2025-06-15T18:29:56+00:00",
        "updatedAt": "2025-06-15T18:29:56+00:00",
        "isActive": True,
    }


@app.get("/vite.svg")
def serve_vite_icon():
    return FileResponse(os.path(FRONTEND_DIR, "vite.svg"))


@app.post("/sites/create", response_model=CreateSiteResponse)
async def create_site(request: CreateSiteRequest):
    now = datetime.now()
    return CreateSiteResponse(
        id=1,
        title=request.title,
        prompt=request.prompt,
        created_at=now,
        updated_at=now,
        view_url="https://ya.ru",
        download_url="https://ya.ru",
        screenshot_url="https://ya.ru",
    )


@app.post("/sites/{site_id}/generate")
async def generate_site(site_id: int, request: GenerateSiteRequest):
    return StreamingResponse(generate_html_stream(), media_type="text/html")


@app.get("/sites/my")
async def get_my_sites():
    now = datetime.now()
    return [
        {
            "id": 1,
            "title": "Сайт о стегозаврах",
            "prompt": "Сайт с информацией о стегозаврах, их питании и видах",
            "created_at": now,
            "updated_at": now,
            "view_url": "https://ya.ru",
            "download_url": "https://ya.ru",
            "screenshot_url": "https://ya.ru",
        },
        {
            "id": 2,
            "title": "Мой блог",
            "prompt": "Блог о программировании на Python",
            "created_at": now,
            "updated_at": now,
            "view_url": "https://ya.ru",
            "download_url": "https://ya.ru",
            "screenshot_url": "https://ya.ru",
        },
        {
            "id": 3,
            "title": "Портфолио",
            "prompt": "Мои работы и проекты",
            "created_at": now,
            "updated_at": now,
            "view_url": "https://ya.ru",
            "download_url": "https://ya.ru",
            "screenshot_url": "https://ya.ru",
        },
    ]


@app.get("/sites/{site_id}")
async def get_site(site_id: int):
    now = datetime.now()
    return {
        "id": site_id,
        "title": "Сайт о стегозаврах",
        "prompt": "Сайт с информацией о стегозаврах, их питании и видах",
        "created_at": now,
        "updated_at": now,
        "view_url": "https://ya.ru",
        "download_url": "https://ya.ru",
        "screenshot_url": "https://ya.ru",
    }
