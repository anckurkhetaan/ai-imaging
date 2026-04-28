"""
Flask web app for Fashn AI Pipeline monitoring and control.
Run with: python app.py
"""
from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
import threading
import logging
from pathlib import Path
from config import Config
from pipeline import Pipeline

app = Flask(__name__)
CORS(app)

# Disable Flask request logging
import logging
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)  # Only show errors, not GET requests

# Global state
pipeline_state = {
    "status": "idle",  # idle, running, stopped
    "current_product": None,
    "current_index": 0,
    "total_products": 0,
    "success_count": 0,
    "fail_count": 0,
    "logs": [],
    "current_step": "",
}

pipeline_thread = None
pipeline_instance = None


class WebLogger(logging.Handler):
    """Custom logger that captures logs for web UI."""
    
    def emit(self, record):
        try:
            log_entry = self.format(record)
            pipeline_state["logs"].append({
                "timestamp": record.created,
                "level": record.levelname,
                "message": log_entry
            })
            # Keep only last 100 logs
            if len(pipeline_state["logs"]) > 100:
                pipeline_state["logs"] = pipeline_state["logs"][-100:]
        except Exception:
            pass  # Silently fail to avoid breaking pipeline


def run_pipeline():
    """Run pipeline in background thread."""
    global pipeline_state, pipeline_instance
    
    try:
        config = Config()  # Changed from Config.from_env()
        pipeline_instance = PipelineWithCallbacks(config)
        pipeline_instance.run()
        
    except Exception as e:
        logging.error(f"Pipeline error: {e}", exc_info=True)
        pipeline_state["status"] = "idle"


class PipelineWithCallbacks(Pipeline):
    """Extended pipeline with progress callbacks for web UI."""
    
    def run(self):
        """Override run to add progress tracking."""
        global pipeline_state
        
        pipeline_state["status"] = "running"
        pipeline_state["logs"] = []
        pipeline_state["success_count"] = 0
        pipeline_state["fail_count"] = 0
        
        logging.info("=" * 60)
        logging.info("FASHN AI PIPELINE - PRODUCTION RUN")
        logging.info("=" * 60)
        
        products = self.sheets.fetch_unprocessed_products()
        total = len(products)
        pipeline_state["total_products"] = total
        
        if total == 0:
            logging.info("No unprocessed products found.")
            pipeline_state["status"] = "idle"
            return
        
        logging.info(f"Found {total} unprocessed products\n")
        
        for idx, product in enumerate(products, 1):
            # Check if stopped
            if pipeline_state["status"] == "stopped":
                logging.info("Pipeline stopped by user")
                break
            
            pipeline_state["current_product"] = product.product_id
            pipeline_state["current_index"] = idx
            
            logging.info(f"\n{'='*60}")
            logging.info(f"PRODUCT {idx}/{total}: {product.product_id}")
            logging.info(f"{'='*60}")
            
            try:
                output_urls = self._process_single_product(product)
                
                if any(output_urls):
                    self.sheets.write_output_urls(product.product_id, output_urls)
                    pipeline_state["success_count"] += 1
                    logging.info(f"[{product.product_id}] SUCCESS")
                else:
                    pipeline_state["fail_count"] += 1
                    logging.warning(f"[{product.product_id}]  FAILED")
                    
            except Exception as e:
                pipeline_state["fail_count"] += 1
                logging.error(f"[{product.product_id}]  FAILED - {e}")
        
        # Final summary
        logging.info(f"\n{'='*60}")
        logging.info(f"PIPELINE COMPLETE")
        logging.info(f"Success: {pipeline_state['success_count']}/{total}")
        logging.info(f"{'='*60}")
        
        pipeline_state["status"] = "idle"


# Setup logging
root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)

# Console handler
console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(message)s"))
root_logger.addHandler(console_handler)

# File handler with UTF-8
file_handler = logging.FileHandler("pipeline.log", encoding='utf-8')
file_handler.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(message)s"))
root_logger.addHandler(file_handler)

# Web handler
web_handler = WebLogger()
web_handler.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(message)s"))
root_logger.addHandler(web_handler)


# Routes
@app.route('/')
def index():
    """Main dashboard page."""
    return render_template('index.html')


@app.route('/api/status')
def get_status():
    """Get current pipeline status."""
    return jsonify(pipeline_state)


@app.route('/api/start', methods=['POST'])
def start_pipeline():
    """Start the pipeline."""
    global pipeline_thread, pipeline_state
    
    if pipeline_state["status"] == "running":
        return jsonify({"error": "Pipeline already running"}), 400
    
    # Set status to running BEFORE starting thread
    pipeline_state["status"] = "running"
    
    # Reset other state
    pipeline_state["current_product"] = None
    pipeline_state["current_index"] = 0
    pipeline_state["total_products"] = 0
    pipeline_state["success_count"] = 0
    pipeline_state["fail_count"] = 0
    pipeline_state["logs"] = []
    pipeline_state["current_step"] = ""
    
    # Start in background thread
    pipeline_thread = threading.Thread(target=run_pipeline, daemon=True)
    pipeline_thread.start()
    
    return jsonify({"message": "Pipeline started"})


@app.route('/api/stop', methods=['POST'])
def stop_pipeline():
    """Stop the pipeline gracefully."""
    global pipeline_state
    
    if pipeline_state["status"] != "running":
        return jsonify({"error": "Pipeline not running"}), 400
    
    pipeline_state["status"] = "stopped"
    return jsonify({"message": "Pipeline stopping..."})


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)