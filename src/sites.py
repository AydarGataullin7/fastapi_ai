from datetime import datetime

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse, StreamingResponse

from src.schemas import CreateSiteRequest, CreateSiteResponse, GenerateSiteRequest
from src.site_generator import generate_site_stream

router = APIRouter()


@router.post("/sites/create", response_model=CreateSiteResponse)
async def create_site(data: CreateSiteRequest, http_request: Request):
    now = datetime.now()
    site_id = len(http_request.app.state.sites) + 1
    http_request.app.state.sites[site_id] = {
        "prompt": data.prompt,
        "screenshot_url": None,
    }
    return CreateSiteResponse(
        id=site_id,
        title=data.title,
        prompt=data.prompt,
        created_at=now,
        updated_at=now,
        view_url="https://google.com",
        download_url="https://google.com",
        screenshot_url="https://google.com",
    )


@router.post("/sites/{site_id}/generate")
async def generate_site(site_id: int, data: GenerateSiteRequest, http_request: Request):
    s3_client = http_request.app.state.s3_client
    gotenberg_client = http_request.app.state.gotenberg_client

    return StreamingResponse(
        generate_site_stream(
            http_request.app.state, site_id, data.prompt, gotenberg_client, s3_client,
        ),
        media_type="text/plain",
    )


@router.get("/sites/my")
async def get_my_sites(http_request: Request):
    now = datetime.now()
    state = http_request.app.state

    sites = []
    for site_id, site_data in state.sites.items():
        view_url = f"http://localhost:9000/fastai/sites/{site_id}/index.html"
        download_url = f"{view_url}?response-content-disposition=attachment"
        sites.append({
            "id": site_id,
            "title": site_data["prompt"],
            "prompt": site_data["prompt"],
            "urlPath": f"/sites/{site_id}",
            "createdAt": now.isoformat(),
            "updatedAt": now.isoformat(),
            "htmlCodeUrl": view_url,
            "htmlCodeDownloadUrl": download_url,
            "screenshotUrl": site_data["screenshot_url"],
        })
    return JSONResponse(content={"sites": sites})


@router.get("/sites/{site_id}")
async def get_site(site_id: int, http_request: Request):
    now = datetime.now()
    state = http_request.app.state

    if site_id not in state.sites:
        raise HTTPException(404, "Сайт не найден")

    site_data = state.sites[site_id]
    view_url = f"http://localhost:9000/fastai/sites/{site_id}/index.html"
    download_url = f"{view_url}?response-content-disposition=attachment"
    return {
        "id": site_id,
        "title": site_data["prompt"],
        "prompt": site_data["prompt"],
        "urlPath": f"/sites/{site_id}",
        "createdAt": now.isoformat(),
        "updatedAt": now.isoformat(),
        "htmlCodeUrl": view_url,
        "htmlCodeDownloadUrl": download_url,
        "screenshotUrl": site_data["screenshot_url"],
    }
