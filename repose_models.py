"""
Repose 5 existing model images to standing front pose.
Preserves face, body, fit, tone - only changes pose.
"""
import os
import time
import requests
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

FASHN_API_KEY = os.environ["FASHN_API_KEY"]
FASHN_BASE_URL = os.getenv("FASHN_BASE_URL", "https://api.fashn.ai/v1")
OUTPUT_DIR = Path("reposed_models")
POLL_INTERVAL = 5
POLL_TIMEOUT = 120

# Upload your 5 images to Cloudinary first, then add URLs here
MODELS_TO_REPOSE = [
    {
        "name": "model_asian_striped_sitting",
        "url": "https://res.cloudinary.com/dti84w6xv/image/upload/v1777386357/__34_dahifc.jpg",  # Image 1 (sitting with striped sweater)
        "prompt": "Change pose to: standing upright facing camera directly, arms relaxed at sides, full body head to toe, natural standing posture, keep exact same face body outfit unchanged, 2:3 aspect ratio"
    },
    {
        "name": "model_asian_halter_top",
        "url": "https://res.cloudinary.com/dti84w6xv/image/upload/v1777386320/__35_xlgjpq.jpg",  # Image 2 (halter top hand on arm)
        "prompt": "Change pose to: standing straight facing camera, arms relaxed at sides naturally, full body head to toe shot, keep exact same face body outfit unchanged, 2:3 aspect ratio"
    },
    {
        "name": "model_european_denim_jacket",
        "url": "https://res.cloudinary.com/dti84w6xv/image/upload/v1777386321/from_zee_tiff_1_oz7u31.jpg",  # Image 3 (denim jacket hand on strap)
        "prompt": "Change pose to: standing upright facing camera, arms at sides relaxed, full body head to toe, keep exact same face body outfit unchanged, 2:3 aspect ratio"
    },
    {
        "name": "model_european_white_tank",
        "url": "https://res.cloudinary.com/dti84w6xv/image/upload/v1777386358/Maria_Rodrigues_ek0i1i.jpg",  # Image 4 (white tank hands in pockets)
        "prompt": "Change pose to: standing straight facing camera directly, arms relaxed at sides, full body head to toe shot, keep exact same face body outfit unchanged, 2:3 aspect ratio"
    },
    {
        "name": "model_european_black_dress",
        "url": "Yhttps://res.cloudinary.com/dti84w6xv/image/upload/v1777386359/model_2_avcd6d.jpg",  # Image 5 (black dress hand on hip)
        "prompt": "Change pose to: standing upright facing camera, arms at sides naturally, full body head to toe, keep exact same face body outfit unchanged, 2:3 aspect ratio"
    },
]


def submit_edit(image_url: str, prompt: str) -> str:
    """Submit edit job to Fashn API."""
    headers = {
        "Authorization": f"Bearer {FASHN_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model_name": "edit",
        "inputs": {
            "image": image_url,  # Changed from model_image
            "prompt": prompt,
            "aspect_ratio": "2:3",
            "output_format": "jpeg",
        },
    }
    response = requests.post(f"{FASHN_BASE_URL}/run", json=payload, headers=headers, timeout=30)
    
    # Add this logging before raise_for_status
    if response.status_code != 200:
        print(f"ERROR: {response.text}")
    
    response.raise_for_status()
    data = response.json()
    if data.get("error"):
        raise RuntimeError(f"API error: {data['error']}")
    return data["id"]


def poll_until_done(job_id: str) -> str:
    """Poll until complete, return output URL."""
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
    
    raise TimeoutError(f"Job {job_id} timed out")


def download_image(url: str, save_path: Path):
    """Download from CDN."""
    response = requests.get(url, timeout=30, stream=True)
    response.raise_for_status()
    with open(save_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)


def main():
    OUTPUT_DIR.mkdir(exist_ok=True)
    print(f"Reposing {len(MODELS_TO_REPOSE)} models...")
    
    for idx, model in enumerate(MODELS_TO_REPOSE, 1):
        print(f"\n[{idx}/{len(MODELS_TO_REPOSE)}] Processing {model['name']}...")
        
        # Submit
        job_id = submit_edit(model['url'], model['prompt'])
        print(f"  Job ID: {job_id}")
        
        # Poll
        output_url = poll_until_done(job_id)
        print(f"  ✓ Complete: {output_url}")
        
        # Download
        save_path = OUTPUT_DIR / f"{model['name']}.jpeg"
        download_image(output_url, save_path)
        print(f"  ✓ Saved: {save_path}")
    
    print(f"\n{'='*50}")
    print(f"✓ All {len(MODELS_TO_REPOSE)} models reposed!")
    print(f"  Location: {OUTPUT_DIR.absolute()}")
    print(f"{'='*50}")


if __name__ == "__main__":
    main()