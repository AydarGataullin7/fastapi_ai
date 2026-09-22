import functools

import html_page_generator._html_page_generator as _hpg  # noqa: PLC2701
import httpx
from langchain_deepseek import ChatDeepSeek


def apply_patches() -> None:
    _hpg.ChatDeepSeek = functools.partial(ChatDeepSeek, max_tokens=65536)

    original_get_images = _hpg.get_images

    async def safe_get_images(keywords: list[str]) -> list[str]:
        query = keywords[0] if keywords else "abstract"
        try:
            return await original_get_images([query])
        except httpx.HTTPStatusError:
            return []

    _hpg.get_images = safe_get_images
