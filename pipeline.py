"""
Main pipeline orchestrator: processes products one at a time.
"""
import logging
from typing import List, Optional
from models.product import Product, ProcessingStatus
from services.sheetservices import SheetService
from services.image_classifier import ImageClassifier
from services.fashion_service import FashnService
from services.storage_service import StorageService
import prompts

logger = logging.getLogger(__name__)


class Pipeline:
    def __init__(self, config):
        self.config = config
        self.sheets = SheetService(config)
        self.classifier = ImageClassifier(config)
        self.fashn = FashnService(config)
        self.storage = StorageService(config)

    def run(self):
        """Main entry point: process all unprocessed products."""
        logger.info("=" * 60)
        logger.info("FASHN AI PIPELINE - PRODUCTION RUN")
        logger.info("=" * 60)
        
        # Fetch unprocessed products
        products = self.sheets.fetch_unprocessed_products()
        total = len(products)
        
        if total == 0:
            logger.info("No unprocessed products found. Exiting.")
            return
        
        logger.info(f"Found {total} unprocessed products\n")
        
        # Process each product individually
        success_count = 0
        fail_count = 0
        
        for idx, product in enumerate(products, 1):
            logger.info(f"\n{'='*60}")
            logger.info(f"PRODUCT {idx}/{total}: {product.product_id}")
            logger.info(f"{'='*60}")
            
            try:
                output_urls = self._process_single_product(product)
                
                # Write to sheet immediately if any URLs succeeded
                if any(output_urls):
                    self.sheets.write_output_urls(product.product_id, output_urls)
                    success_count += 1
                    logger.info(f"[{product.product_id}] COMPLETE - Sheet updated")
                else:
                    fail_count += 1
                    logger.warning(f"[{product.product_id}] FAILED - No outputs generated")
                    
            except Exception as e:
                fail_count += 1
                logger.error(f"[{product.product_id}] FAILED - {e}", exc_info=True)
        
        # Final summary
        logger.info(f"\n{'='*60}")
        logger.info(f"PIPELINE COMPLETE")
        logger.info(f"{'='*60}")
        logger.info(f"Total Products: {total}")
        logger.info(f"Success: {success_count}")
        logger.info(f"Failed: {fail_count}")
        logger.info(f"Success Rate: {success_count/total*100:.1f}%")
        logger.info(f"{'='*60}")

    def _process_single_product(self, product: Product) -> List[Optional[str]]:
        """
        Process one product through the entire pipeline.
        Returns list of 3 Cloudinary URLs (or None for failed views).
        """
        # Step 1: Classify input images
        logger.info(f"[{product.product_id}] Step 1/4: Classifying inputs...")
        classified = self.classifier.classify_views(product.raw_image_urls)
        
        front_input = classified.get("front")
        back_input = classified.get("back")
        side_input = classified.get("side")
        has_back_input = back_input is not None
        
        logger.info(f"[{product.product_id}] Detected: front={bool(front_input)}, back={bool(back_input)}, side={bool(side_input)}")
        
        # Fallback: use first input for all views if classification failed
        fallback_url = product.raw_image_urls[0] if product.raw_image_urls else None
        front_product = front_input or fallback_url
        back_product = back_input or fallback_url
        side_product = side_input or fallback_url
        
        if not front_product:
            raise ValueError("No product input available")
        
        # Step 2: Build prompts
        logger.info(f"[{product.product_id}] Step 2/4: Building prompts...")
        prompt_front = prompts.front_prompt(product.category, product.model_index)
        prompt_back = (prompts.back_prompt_with_input(product.category, product.model_index) 
                      if has_back_input 
                      else prompts.back_prompt_no_input(product.category, product.model_index))
        prompt_side = prompts.side_prompt(product.category, product.model_index)
        
        # Step 3: Generate all 3 views
        logger.info(f"[{product.product_id}] Step 3/4: Generating 3 views...")
        total_credits = 0
        output_urls = []
        
        view_configs = [
            ("front", front_product, prompt_front),
            ("back", back_product, prompt_back),
            ("side", side_product, prompt_side),
        ]
        
        for view_idx, (view_name, product_url, prompt) in enumerate(view_configs, 1):
            try:
                logger.info(f"[{product.product_id}] Generating {view_name} (view_{view_idx})...")
                
                # Generate with Fashn
                cdn_url, credits = self.fashn.generate_view(
                    product_id=product.product_id,
                    product_index=product.model_index,
                    view_name=view_name,
                    product_url=product_url,
                    prompt=prompt
                )
                total_credits += credits
                logger.info(f"[{product.product_id}]     Fashn complete: {credits} credits")
                
                # Upload to Cloudinary
                cloudinary_url = self.storage.save(
                    product_id=product.product_id,
                    view_index=view_idx,
                    cdn_url=cdn_url
                )
                
                if cloudinary_url:
                    output_urls.append(cloudinary_url)
                    logger.info(f"[{product.product_id}]     Ok {view_name} complete")
                else:
                    output_urls.append(None)
                    logger.warning(f"[{product.product_id}]     Fail {view_name} storage failed")
                
            except Exception as e:
                logger.error(f"[{product.product_id}]     Fail {view_name} failed: {e}")
                output_urls.append(None)
        
        # Step 4: Summary
        logger.info(f"[{product.product_id}] Step 4/4: Complete")
        logger.info(f"[{product.product_id}] Total credits used: {total_credits}")
        logger.info(f"[{product.product_id}] Successful views: {sum(1 for url in output_urls if url)}/3")
        
        return output_urls