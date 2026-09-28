import os

from fastapi import APIRouter
from fastapi.responses import FileResponse

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")

router = APIRouter()


@router.get("/")
def serve_index():
    return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))


@router.get("/frontend-settings.json")
def serve_settings():
    return FileResponse(os.path.join(FRONTEND_DIR, "frontend-settings.json"))


@router.get("/vite.svg")
def serve_vite_icon():
    return FileResponse(os.path.join(FRONTEND_DIR, "vite.svg"))
