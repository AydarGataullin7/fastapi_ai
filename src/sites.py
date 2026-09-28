from datetime import datetime

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, StreamingResponse

from src.schemas import CreateSiteRequest, CreateSiteResponse, GenerateSiteRequest
from src.site_generator import generate_site_stream

router = APIRouter()


@router.post("/sites/create", response_model=CreateSiteResponse)
async def create_site(request: CreateSiteRequest):
    now = datetime.now()
    return CreateSiteResponse(
        id=1,
        title=request.title,
        prompt=request.prompt,
        created_at=now,
        updated_at=now,
        view_url="https://google.com",
        download_url="https://google.com",
        screenshot_url="https://google.com",
    )


@router.post("/sites/{site_id}/generate")
async def generate_site(site_id: int, request: GenerateSiteRequest, http_request: Request):
    s3_client = http_request.app.state.s3_client
    gotenberg_client = http_request.app.state.gotenberg_client

    return StreamingResponse(
        generate_site_stream(
            http_request.app.state, site_id, request.prompt, gotenberg_client, s3_client,
        ),
        media_type="text/plain",
    )


@router.get("/sites/my")
async def get_my_sites(http_request: Request):
    now = datetime.now()
    site_id = 1
    view_url = f"http://localhost:9000/fastai/sites/{site_id}/index.html"
    download_url = f"{view_url}?response-content-disposition=attachment"

    state = http_request.app.state
    sites = [
        {
            "id": site_id,
            "title": state.last_prompt,
            "prompt": state.last_prompt,
            "urlPath": f"/sites/{site_id}",
            "createdAt": now.isoformat(),
            "updatedAt": now.isoformat(),
            "htmlCodeUrl": view_url,
            "htmlCodeDownloadUrl": download_url,
            "screenshotUrl": state.last_screenshot_url,
        },
    ]
    return JSONResponse(content={"sites": sites})


@router.get("/sites/{site_id}")
async def get_site(site_id: int, http_request: Request):
    now = datetime.now()
    view_url = f"http://localhost:9000/fastai/sites/{site_id}/index.html"
    download_url = f"{view_url}?response-content-disposition=attachment"

    state = http_request.app.state
    return {
        "id": site_id,
        "title": state.last_prompt,
        "prompt": state.last_prompt,
        "urlPath": f"/sites/{site_id}",
        "createdAt": now.isoformat(),
        "updatedAt": now.isoformat(),
        "htmlCodeUrl": view_url,
        "htmlCodeDownloadUrl": download_url,
        "screenshotUrl": state.last_screenshot_url,
    }
