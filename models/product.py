from dataclasses import dataclass, field
from typing import List
from enum import Enum


class ImageType(str, Enum):
    PRODUCT_ONLY = "product_only"   # flat lay, hanger, ghost mannequin → product-to-model
    ON_MODEL = "on_model"           # person detected → model-swap
    UNKNOWN = "unknown"             # before classification


class ProcessingStatus(str, Enum):
    PENDING = "pending"
    CLASSIFIED = "classified"
    SUBMITTED = "submitted"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class ImageRecord:
    product_id: str
    view_index: int                        # 1, 2, or 3
    source_url: str
    image_type: ImageType = ImageType.UNKNOWN
    assigned_prompt: str = ""
    fashn_job_id: str = ""
    output_local_path: str = ""
    output_cloudinary_url: str = ""
    status: ProcessingStatus = ProcessingStatus.PENDING
    error_message: str = ""


@dataclass
class Product:
    product_id: str
    category: str
    raw_image_urls: List[str]
    model_index: int = 0
    images: List[ImageRecord] = field(default_factory=list)

    def assign_prompt(self, prompt_profiles: List[str]) -> str:
        """Round-robin prompt profile selection based on product position."""
        return prompt_profiles[self.model_index % len(prompt_profiles)]

    def build_image_records(self) -> None:
        """Convert raw URLs into ImageRecord objects."""
        self.images = [
            ImageRecord(
                product_id=self.product_id,
                view_index=idx + 1,
                source_url=url.strip()
            )
            for idx, url in enumerate(self.raw_image_urls)
            if url and url.strip()
        ]