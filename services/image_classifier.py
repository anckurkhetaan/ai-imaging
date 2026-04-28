import base64
import logging
import requests
from typing import Dict, List

logger = logging.getLogger(__name__)

ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"

VIEW_CLASSIFICATION_PROMPT = """You are a fashion product image analyzer.

Look at this garment image and identify which VIEW it shows:
- FRONT: Shows the front design of the garment (neckline, front buttons, main graphic, etc.)
- BACK: Shows the back design of the garment (back neckline, back details, rear view)
- SIDE: Shows the side profile of the garment

Reply with ONLY ONE WORD: front, back, or side"""


class ImageClassifier:
    def __init__(self, config):
        self.config = config

    # ------------------------------------------------------------------ #
    # Internal helpers
    # ------------------------------------------------------------------ #

    def _fetch_image_as_base64(self, url: str) -> tuple[str, str]:
        """Download image from URL and return (base64_data, media_type)."""
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        content_type = response.headers.get("Content-Type", "image/jpeg").split(";")[0].strip()
        b64 = base64.standard_b64encode(response.content).decode("utf-8")
        return b64, content_type

    def _call_claude_vision(self, b64_data: str, media_type: str, prompt: str) -> str:
        """Send image to Claude Vision and return raw text response."""
        headers = {
            "x-api-key": self.config.claude_api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
        payload = {
            "model": self.config.claude_vision_model,
            "max_tokens": 10,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": media_type,
                                "data": b64_data,
                            },
                        },
                        {"type": "text", "text": prompt},
                    ],
                }
            ],
        }
        response = requests.post(ANTHROPIC_API_URL, json=payload, headers=headers, timeout=30)
        if response.status_code != 200:
            logger.error(f"Anthropic API error {response.status_code}: {response.text}")
        response.raise_for_status()
        return response.json()["content"][0]["text"].strip().lower()
    
    # ------------------------------------------------------------------ #
    # Public
    # ------------------------------------------------------------------ #

    def classify_views(self, image_urls: List[str]) -> Dict[str, str]:
        """
        Classify each input image as front/back/side.
        Returns dict: {'front': url, 'back': url, 'side': url} or None if view missing.
        """
        view_map = {"front": None, "back": None, "side": None}
        
        for url in image_urls:
            try:
                b64_data, media_type = self._fetch_image_as_base64(url)
                result = self._call_claude_vision(b64_data, media_type, VIEW_CLASSIFICATION_PROMPT)
                
                if "front" in result:
                    view_map["front"] = url
                    logger.info(f"Classified as FRONT: {url}")
                elif "back" in result:
                    view_map["back"] = url
                    logger.info(f"Classified as BACK: {url}")
                elif "side" in result:
                    view_map["side"] = url
                    logger.info(f"Classified as SIDE: {url}")
                else:
                    logger.warning(f"Unclear classification for {url}: {result}")
            except requests.exceptions.HTTPError as e:
                logger.warning(f"Classification failed for {url}: {e}")
                if hasattr(e, 'response') and e.response:
                    logger.error(f"API response: {e.response.text}")
            except Exception as e:
                logger.warning(f"Classification failed for {url}: {e}")
        
        return view_map