"""
Storage service: saves generated images locally and/or to Cloudinary.
"""
import os
import logging
import requests
from pathlib import Path
from typing import Optional
import cloudinary
import cloudinary.uploader

logger = logging.getLogger(__name__)


class StorageService:
    def __init__(self, config):
        self.config = config
        self.output_dir = Path(config.output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Initialize Cloudinary if enabled
        if config.use_cloudinary:
            cloudinary.config(
                cloud_name=config.cloudinary_cloud_name,
                api_key=config.cloudinary_api_key,
                api_secret=config.cloudinary_api_secret,
            )
            logger.info("Cloudinary initialized")
        else:
            logger.info("Cloudinary disabled - local storage only")

    def save(self, product_id: str, view_index: int, cdn_url: str) -> Optional[str]:
        """
        Download from Fashn CDN and upload to Cloudinary.
        Returns Cloudinary URL or None if failed.
        
        Args:
            product_id: Product identifier
            view_index: 1, 2, or 3 (front, back, side)
            cdn_url: Fashn CDN URL to download from
        """
        try:
            # Create product folder
            product_folder = self.output_dir / product_id
            product_folder.mkdir(exist_ok=True)
            
            # Download from Fashn CDN to local temp
            local_path = product_folder / f"view_{view_index}.jpeg"
            self._download_image(cdn_url, local_path)
            logger.debug(f"[{product_id}] Downloaded view_{view_index} locally")
            
            # Upload to Cloudinary if enabled
            if self.config.use_cloudinary:
                cloudinary_url = self._upload_to_cloudinary(
                    local_path, 
                    product_id, 
                    view_index
                )
                logger.info(f"[{product_id}] view_{view_index} → Cloudinary ✓")
                return cloudinary_url
            else:
                logger.info(f"[{product_id}] view_{view_index} → Local only")
                return str(local_path)
                
        except Exception as e:
            logger.error(f"[{product_id}] Storage failed for view_{view_index}: {e}")
            return None

    def _download_image(self, url: str, save_path: Path):
        """Download image from URL to local path."""
        response = requests.get(url, timeout=30, stream=True)
        response.raise_for_status()
        with open(save_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

    def _upload_to_cloudinary(self, local_path: Path, product_id: str, view_index: int) -> str:
        """Upload to Cloudinary and return public URL."""
        public_id = f"{self.config.cloudinary_folder}/{product_id}_{view_index}"
        
        result = cloudinary.uploader.upload(
            str(local_path),
            public_id=public_id,
            overwrite=True,
            resource_type="image",
        )
    
        return result["secure_url"]