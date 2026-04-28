import csv
import logging
import os
from datetime import datetime
from pathlib import Path
from models.product import ImageRecord

logger = logging.getLogger(__name__)

CSV_FIELDS = [
    "timestamp",
    "product_id",
    "view_index",
    "image_type",
    "source_url",
    "assigned_prompt",
    "fashn_job_id",
    "status",
    "output_local_path",
    "output_cloudinary_url",
    "error_message",
]


class LoggerService:
    def __init__(self, config):
        self.log_path = Path(config.log_file)
        self._ensure_file()

    # ------------------------------------------------------------------ #
    # Internal
    # ------------------------------------------------------------------ #

    def _ensure_file(self) -> None:
        """Create CSV with headers if it doesn't exist yet."""
        if not self.log_path.exists():
            with open(self.log_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
                writer.writeheader()
            logger.info(f"Run log created at: {self.log_path}")

    # ------------------------------------------------------------------ #
    # Public
    # ------------------------------------------------------------------ #

    def log(self, image: ImageRecord) -> None:
        """Append one row to the CSV log for a processed ImageRecord."""
        row = {
            "timestamp": datetime.utcnow().isoformat(),
            "product_id": image.product_id,
            "view_index": image.view_index,
            "image_type": image.image_type.value,
            "source_url": image.source_url,
            "assigned_prompt": image.assigned_prompt,
            "fashn_job_id": image.fashn_job_id,
            "status": image.status.value,
            "output_local_path": image.output_local_path,
            "output_cloudinary_url": image.output_cloudinary_url,
            "error_message": image.error_message,
        }
        with open(self.log_path, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
            writer.writerow(row)

    def log_batch_summary(self, total: int, success: int, failed: int) -> None:
        """Print a clean summary after each batch run."""
        logger.info("=" * 50)
        logger.info(f"BATCH COMPLETE — {datetime.utcnow().isoformat()}")
        logger.info(f"  Total products : {total}")
        logger.info(f"  Succeeded      : {success}")
        logger.info(f"  Failed         : {failed}")
        logger.info(f"  Log saved to   : {self.log_path}")
        logger.info("=" * 50)