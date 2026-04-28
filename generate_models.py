"""
One-time setup script to generate model library.
Run once: python generate_models.py
"""
import os
import time
import logging
import requests
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

# Config
FASHN_API_KEY = os.environ["FASHN_API_KEY"]
FASHN_BASE_URL = os.getenv("FASHN_BASE_URL", "https://api.fashn.ai/v1")
MODEL_LIBRARY_DIR = Path("model_library")
POLL_INTERVAL = 5
POLL_TIMEOUT = 120

# 2 European models with brand voice (mid-premium accessible, clean white/grey studio)
MODEL_PROMPTS = [
    "European woman mid-30s, 5'8 height, athletic inverted triangle build broad shoulders narrow hips, black pixie cut edgy asymmetric, angular face shape prominent cheekbones sharp features, Scandinavian features icy blue eyes, minimal makeup nude lips, porcelain fair skin, wearing black ribbed bodysuit with high-waisted distressed denim, black leather ankle boots, full body standing arms at sides modern editorial stance, white seamless studio background, bright clean lighting, contemporary fashion catalog, ultra sharp"
]


def submit_model_create(prompt: str) -> str:
    """Submit model-create job and return job ID."""
    headers = {
        "Authorization": f"Bearer {FASHN_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model_name": "model-create",
        "inputs": {
            "prompt": prompt,
            "aspect_ratio": "2:3",  # Standard fashion model ratio
            "output_format": "jpeg",
        },
    }
    response = requests.post(f"{FASHN_BASE_URL}/run", json=payload, headers=headers, timeout=30)
    response.raise_for_status()
    data = response.json()
    if data.get("error"):
        raise RuntimeError(f"API error: {data['error']}")
    return data["id"]


def poll_until_done(job_id: str) -> str:
    """Poll until complete and return CDN URL."""
    headers = {"Authorization": f"Bearer {FASHN_API_KEY}"}
    elapsed = 0
    while elapsed < POLL_TIMEOUT:
        response = requests.get(f"{FASHN_BASE_URL}/status/{job_id}", headers=headers, timeout=15)
        response.raise_for_status()
        data = response.json()
        status = data.get("status")
        
        if status == "completed":
            return data["output"][0]
        elif status == "failed":
            raise RuntimeError(f"Job failed: {data.get('error')}")
        
        time.sleep(POLL_INTERVAL)
        elapsed += POLL_INTERVAL
    
    raise TimeoutError(f"Job {job_id} timed out after {POLL_TIMEOUT}s")


def download_model(cdn_url: str, save_path: Path) -> None:
    """Download model image from CDN."""
    response = requests.get(cdn_url, timeout=30, stream=True)
    response.raise_for_status()
    with open(save_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)


def main():
    MODEL_LIBRARY_DIR.mkdir(exist_ok=True)
    logger.info(f"Generating {len(MODEL_PROMPTS)} models...")
    
    for idx, prompt in enumerate(MODEL_PROMPTS, start=1):
        logger.info(f"\n[{idx}/{len(MODEL_PROMPTS)}] Creating model...")
        logger.info(f"Prompt: {prompt[:80]}...")
        
        # Submit
        job_id = submit_model_create(prompt)
        logger.info(f"Job ID: {job_id}")
        
        # Poll
        cdn_url = poll_until_done(job_id)
        logger.info(f"✓ Complete: {cdn_url}")
        
        # Download
        save_path = MODEL_LIBRARY_DIR / f"model_{idx}.jpeg"
        download_model(cdn_url, save_path)
        logger.info(f"✓ Saved to: {save_path}")
    
    logger.info(f"\n{'='*50}")
    logger.info(f"✓ All models generated successfully!")
    logger.info(f"  Location: {MODEL_LIBRARY_DIR.absolute()}")
    logger.info(f"  Files: {list(MODEL_LIBRARY_DIR.glob('*.jpeg'))}")
    logger.info(f"\nNext step: Add to .env:")
    logger.info(f"  MODEL_LIBRARY_DIR=model_library")
    logger.info(f"{'='*50}")


if __name__ == "__main__":
    main()