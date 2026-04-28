import time
import logging
import requests
from typing import Optional

logger = logging.getLogger(__name__)

TERMINAL_STATUSES = {"completed", "failed"}


class FashnService:
    def __init__(self, config):
        self.config = config
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.config.fashn_api_key}",
            "Content-Type": "application/json",
        })
        self.model_urls = config.model_urls
        logger.info(f"Loaded {len(self.model_urls)} model URLs from config")

    # ------------------------------------------------------------------ #
    # Internal helpers
    # ------------------------------------------------------------------ #

    def _get_model_for_product(self, product_index: int) -> str:
        """Return model URL using round-robin."""
        return self.model_urls[product_index % len(self.model_urls)]

    def _run_url(self) -> str:
        return f"{self.config.fashn_base_url}/run"

    def _status_url(self, job_id: str) -> str:
        return f"{self.config.fashn_base_url}/status/{job_id}"

    def _submit_product_to_model(self, model_url: str, product_url: str, prompt: str) -> str:
        """Submit product-to-model job with model_image. Returns job ID."""
        payload = {
            "model_name": "product-to-model",
            "inputs": {
                "model_image": model_url,
                "product_image": product_url,
                "prompt": prompt,
                "aspect_ratio": "2:3",
                "resolution": "1k",  # ADD THIS LINE
                "output_format": self.config.fashn_output_format,
        },
}

        
        logger.debug(f"Submitting payload: {payload}")
        response = self.session.post(self._run_url(), json=payload, timeout=30)
        
        # Log full response for debugging
        try:
            response.raise_for_status()
        except requests.HTTPError as e:
            logger.error(f"Fashn API error response: {response.text}")
            raise
        
        data = response.json()
        if data.get("error"):
            raise RuntimeError(f"Fashn API error on submit: {data['error']}")
        return data["id"]

    def _poll_until_done(self, job_id: str) -> tuple[dict, int]:
        """
        Poll /status/{id} until terminal state or timeout.
        Returns (status_response_dict, credits_used).
        """
        elapsed = 0
        credits_used = 0
        
        while elapsed < self.config.fashn_poll_timeout:
            response = self.session.get(self._status_url(job_id), timeout=15)
            response.raise_for_status()
            
            # Extract credits from header
            credits_header = response.headers.get("x-fashn-credits-used")
            if credits_header:
                try:
                    credits_used = int(credits_header)
                except ValueError:
                    pass
            
            data = response.json()
            status = data.get("status", "")
            logger.debug(f"Job {job_id} status: {status} ({elapsed}s elapsed)")

            if status in TERMINAL_STATUSES:
                return data, credits_used

            time.sleep(self.config.fashn_poll_interval)
            elapsed += self.config.fashn_poll_interval

        raise TimeoutError(f"Job {job_id} did not complete within {self.config.fashn_poll_timeout}s")

    # ------------------------------------------------------------------ #
    # Public
    # ------------------------------------------------------------------ #

    def generate_view(
        self, 
        product_id: str, 
        product_index: int,
        view_name: str,
        product_url: str,
        prompt: str
    ) -> tuple[str, int]:
        """
        Generate a single view (front/back/side) using product-to-model.
        Returns (output_cdn_url, credits_consumed).
        """
        model_url = self._get_model_for_product(product_index)
        logger.info(f"[{product_id}] Generating {view_name} using model {model_url[:60]}...")
        
        try:
            job_id = self._submit_product_to_model(model_url, product_url, prompt)
            logger.info(f"[{product_id}] {view_name} job submitted: {job_id}")
            
            result, credits = self._poll_until_done(job_id)
            
            if result["status"] == "completed":
                output_url = result["output"][0]
                logger.info(f"[{product_id}] {view_name} completed → {credits} credits used")
                return output_url, credits
            else:
                error = result.get("error", {})
                raise RuntimeError(f"Job failed: {error.get('name')} — {error.get('message')}")
                
        except Exception as e:
            logger.error(f"[{product_id}] {view_name} generation failed: {e}")
            raise