import logging
import os

import httpx
from botocore.exceptions import BotoCoreError, ClientError
from gotenberg_api import GotenbergServerError, ScreenshotHTMLRequest
from html_page_generator import AsyncPageGenerator

from src.env_settings import settings
from src.s3_client import upload_file_o_s3

logger = logging.getLogger(__name__)

HTTP_500_INTERNAL_SERVER_ERROR = 500


def _chunk_to_str(chunk) -> str:
    if isinstance(chunk, str):
        return chunk
    if isinstance(chunk, list):
        return "".join(_chunk_to_str(item) for item in chunk)
    if hasattr(chunk, "content"):
        content = chunk.content
        if isinstance(content, str):
            return content
        return str(content)
    return str(chunk)


def _clean_html(content: str) -> str:
    start = content.find("<!DOCTYPE html>")
    if start == -1:
        start = content.find("<html>")
    if start == -1:
        return content
    return content[start:]


async def _generate_and_upload_screenshot(
    site_id: int,
    html_code: str,
    gotenberg_client: httpx.AsyncClient,
    s3_client,
) -> str | None:
    try:
        screenshot_bytes = await ScreenshotHTMLRequest(
            index_html=html_code,
            width=settings.gotenberg.width,
            format=settings.gotenberg.format,
            wait_delay=settings.gotenberg.wait_delay,
        ).asend(gotenberg_client)
    except GotenbergServerError as e:
        logger.error("Gotenberg error: %s", e)
        return None

    try:
        screenshot_path = f"screenshot_{site_id}.png"
        with open(screenshot_path, "wb") as f:
            f.write(screenshot_bytes)

        screenshot_url = await upload_file_o_s3(
            client=s3_client,
            file_path=screenshot_path,
            key=f"sites/{site_id}/screenshot.png",
            bucket=settings.s3.bucket,
            endpoint=settings.s3.endpoint,
            content_type="image/png",
            content_disposition="inline",
        )
        os.remove(screenshot_path)
        return screenshot_url
    except (ClientError, BotoCoreError, OSError) as e:
        logger.error("Screenshot upload error: %s", e)
        return None


async def _upload_site_after_generation(
    state,
    site_id: int,
    html_code: str,
    gotenberg_client: httpx.AsyncClient,
    s3_client,
) -> None:
    try:
        with open("index.html", "w", encoding="utf-8") as file:
            file.write(html_code)
    except OSError as e:
        logger.error("Failed to write index.html: %s", e)
        return

    try:
        await upload_file_o_s3(
            client=s3_client,
            file_path="index.html",
            key=f"sites/{site_id}/index.html",
            bucket=settings.s3.bucket,
            endpoint=settings.s3.endpoint,
            content_type="text/html",
            content_disposition="inline",
        )
    except (ClientError, BotoCoreError, OSError) as e:
        logger.error("S3 error: %s", e)

    screenshot_url = await _generate_and_upload_screenshot(
        site_id, html_code, gotenberg_client, s3_client,
    )
    state.last_screenshot_url = screenshot_url


async def generate_site_stream(
    state,
    site_id: int,
    prompt: str,
    gotenberg_client: httpx.AsyncClient,
    s3_client,
):
    state.last_prompt = prompt

    generator = AsyncPageGenerator(debug_mode=True)

    try:
        async for chunk in generator(prompt):
            yield _chunk_to_str(chunk)
    except httpx.HTTPStatusError as e:
        if e.response.status_code == HTTP_500_INTERNAL_SERVER_ERROR:
            simple_prompt = prompt.split(maxsplit=1)[0] if prompt.split() else "site"
            generator = AsyncPageGenerator(debug_mode=True)
            async for chunk in generator(simple_prompt):
                yield _chunk_to_str(chunk)
        else:
            raise

    html_code = _clean_html(generator.html_page.html_code)

    await _upload_site_after_generation(
        state, site_id, html_code, gotenberg_client, s3_client,
    )
