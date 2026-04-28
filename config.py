import os
from dataclasses import dataclass, field
from typing import List
from dotenv import load_dotenv

load_dotenv()


@dataclass
class Config:
    # Fashn AI
    fashn_api_key: str = field(default_factory=lambda: os.environ["FASHN_API_KEY"])
    fashn_base_url: str = field(default_factory=lambda: os.getenv("FASHN_BASE_URL", "https://api.fashn.ai/v1"))
    fashn_poll_interval: int = field(default_factory=lambda: int(os.getenv("FASHN_POLL_INTERVAL_SEC", "5")))
    fashn_poll_timeout: int = field(default_factory=lambda: int(os.getenv("FASHN_POLL_TIMEOUT_SEC", "120")))

    # 6 brand-aligned prompt profiles — each as its own env variable
    prompt_profiles: List[str] = field(default_factory=lambda: [
        os.environ[f"FASHN_PROMPT_{i}"] for i in range(1, 7)
    ])

    # Google Sheets
    gsheet_credentials_path: str = field(default_factory=lambda: os.environ["GSHEET_CREDENTIALS_PATH"])
    gsheet_spreadsheet_id: str = field(default_factory=lambda: os.environ["GSHEET_SPREADSHEET_ID"])
    gsheet_sheet_name: str = field(default_factory=lambda: os.getenv("GSHEET_SHEET_NAME", "Sheet1"))

    # Column names in the sheet (configurable)
    col_product_id: str = field(default_factory=lambda: os.getenv("COL_PRODUCT_ID", "product_id"))
    col_category: str = field(default_factory=lambda: os.getenv("COL_CATEGORY", "category"))
    col_image_links: List[str] = field(default_factory=lambda: os.getenv(
        "COL_IMAGE_LINKS", "image_link_1,image_link_2,image_link_3"
    ).split(","))

    # Output
    output_dir: str = field(default_factory=lambda: os.getenv("OUTPUT_DIR", "outputs"))
    log_file: str = field(default_factory=lambda: os.getenv("LOG_FILE", "run_log.csv"))

    # Cloudinary (Phase 2 — optional)
    cloudinary_cloud_name: str = field(default_factory=lambda: os.getenv("CLOUDINARY_CLOUD_NAME", ""))
    cloudinary_api_key: str = field(default_factory=lambda: os.getenv("CLOUDINARY_API_KEY", ""))
    cloudinary_api_secret: str = field(default_factory=lambda: os.getenv("CLOUDINARY_API_SECRET", ""))
    use_cloudinary: bool = field(default_factory=lambda: os.getenv("USE_CLOUDINARY", "false").lower() == "true")

    # Concurrency
    max_concurrent_requests: int = field(default_factory=lambda: int(os.getenv("MAX_CONCURRENT_REQUESTS", "5")))


    # Output columns written back to sheet
    col_output_images: List[str] = field(default_factory=lambda: os.getenv(
        "COL_OUTPUT_IMAGES", "output_image_1,output_image_2,output_image_3"
    ).split(","))

    # Claude Vision (image classification)
    claude_api_key: str = field(default_factory=lambda: os.environ["ANTHROPIC_API_KEY"])
    claude_vision_model: str = field(default_factory=lambda: os.getenv(
        "CLAUDE_VISION_MODEL", "claude-haiku-4-5-20251001"
    ))

    # Fashn output format
    fashn_output_format: str = field(default_factory=lambda: os.getenv("FASHN_OUTPUT_FORMAT", "jpeg"))

    # Cloudinary folder (Phase 2)
    cloudinary_folder: str = field(default_factory=lambda: os.getenv("CLOUDINARY_FOLDER", "fashn_outputs"))

    # Model library
    model_library_dir: str = field(default_factory=lambda: os.getenv("MODEL_LIBRARY_DIR", "model_library"))

    # Model library URLs (Cloudinary)
    model_urls: List[str] = field(default_factory=lambda: [
        os.environ[f"MODEL_{i}_URL"] for i in range(1, 13)  # Changed from 1,3 to 1,13
    ])

    # View-specific prompts
    prompt_front: str = field(default_factory=lambda: os.environ["PROMPT_FRONT"])
    prompt_back: str = field(default_factory=lambda: os.environ["PROMPT_BACK"])
    prompt_side: str = field(default_factory=lambda: os.environ["PROMPT_SIDE"])