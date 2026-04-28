# Fashn AI Product-to-Model Pipeline

Automated fashion product photography pipeline using Fashn AI. Transforms product images into professional model shots with multiple views (front, back, side).

## Features

- 🤖 **Automated Processing**: Google Sheets → Claude Vision → Fashn AI → Cloudinary
- 👗 **Multi-View Generation**: Front, back, and side views for each product
- 🎨 **12 Model Library**: Rotating European women models with diverse styles
- 🖼️ **Instagram Poses**: 5 natural pose variations per view
- ☁️ **Cloudinary Integration**: Automatic upload to BrownButter folder
- 🌐 **Web Dashboard**: Real-time monitoring with start/stop controls
- 📊 **Progress Tracking**: Live logs and success/fail statistics

## Architecture

```
Google Sheets (Input)
    ↓
Claude Vision (Classify: front/back/side)
    ↓
Fashn AI Product-to-Model (Generate 3 views)
    ↓
Cloudinary Storage (BrownButter folder)
    ↓
Google Sheets (Output URLs)
```

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Copy `.env.example` to `.env` and fill in:

```env
# Fashn API
FASHN_API_KEY=your_fashn_api_key

# Google Sheets
GSHEET_CREDENTIALS_PATH=credentials.json
GSHEET_SPREADSHEET_ID=your_spreadsheet_id
GSHEET_SHEET_NAME=ImageBank

# Claude Vision
ANTHROPIC_API_KEY=your_anthropic_api_key

# Cloudinary
USE_CLOUDINARY=true
CLOUDINARY_CLOUD_NAME=your_cloud_name
CLOUDINARY_API_KEY=your_api_key
CLOUDINARY_API_SECRET=your_api_secret
CLOUDINARY_FOLDER=BrownButter

# Model Library (12 Cloudinary URLs)
MODEL_1_URL=https://res.cloudinary.com/.../model_woman_casual_blonde_1.jpg
MODEL_2_URL=https://res.cloudinary.com/.../model_woman_casual_brunette_2.jpg
# ... MODEL_3_URL through MODEL_12_URL
```

### 3. Google Sheets Setup

1. Create a service account in Google Cloud Console
2. Enable Google Sheets API + Google Drive API
3. Download `credentials.json` to project root
4. Share your spreadsheet with the service account email (Editor access)

**Required Columns:**
- `New_Product_Id` - Product identifier
- `Sub_Category_Name` - Category (dress, top, pants, etc.)
- `Product_Image_Main_URL` - First product image
- `Second_Image_Ifany` - Second image (optional)
- `Third_Image_Ifany` - Third image (optional)
- `output_image_1` - Front view output (auto-created)
- `output_image_2` - Back view output (auto-created)
- `output_image_3` - Side view output (auto-created)

### 4. Generate Model Library (One-Time)

```bash
python generate_models.py
```

This creates 12 European women models and uploads them to Cloudinary.

## Usage

### Web Dashboard (Recommended)

```bash
python app.py
```

Open `http://localhost:5000` in your browser.

- Click **▶ Start Pipeline** to process all unprocessed products
- Watch real-time progress, logs, and statistics
- Click **⏹ Stop Pipeline** to gracefully halt

### Command Line

```bash
python main.py
```

Processes products sequentially with console output.

## Pipeline Flow

For each product:

1. **Classify Inputs** (Claude Vision)
   - Identifies front/back/side views from input images
   - Fallback: uses first image for all views if classification fails

2. **Build Prompts**
   - Selects pose from 5-pose library (rotates by product index)
   - Category-aware footwear (dresses→heels, pants→sneakers)
   - Smart back handling (conservative if no back input detected)

3. **Generate Views** (Fashn API)
   - 3 views per product using product-to-model endpoint
   - 2:3 aspect ratio, 2k resolution
   - ~6 credits per product (2 credits/view)

4. **Upload to Cloudinary**
   - Saves to `BrownButter/{product_id}_1/2/3`
   - Returns secure HTTPS URLs

5. **Update Google Sheet**
   - Writes Cloudinary URLs to output columns
   - Skips products with existing outputs

## Cost Analysis

**Per Product:**
- Claude Vision: ~$0.001 (negligible)
- Fashn API: 6 credits (~$0.45)
- **Total: ~$0.45/product**

**For 100 products/day:**
- 600 Fashn credits
- ~$45/day

## File Structure

```
fashn_pipeline/
├── app.py                      # Flask web dashboard
├── main.py                     # CLI entry point
├── pipeline.py                 # Main orchestrator
├── config.py                   # Configuration from .env
├── prompts.py                  # Pose library (5 poses × 3 views)
├── models/
│   └── product.py              # Product & ImageRecord dataclasses
├── services/
│   ├── sheetservices.py        # Google Sheets I/O
│   ├── image_classifier.py     # Claude Vision classification
│   ├── fashion_service.py      # Fashn API integration
│   └── storage_service.py      # Cloudinary upload
├── templates/
│   └── index.html              # Web dashboard UI
├── generate_models.py          # Model library generator
├── repose_models.py            # Edit API for pose correction
└── requirements.txt
```

## Configuration Options

### Pose Library

Edit `prompts.py` to customize poses:
- `FRONT_POSES`: 5 variations (hand in hair, arms crossed, etc.)
- `BACK_POSES`: 5 variations (over shoulder, hands in hair, etc.)
- `SIDE_POSES`: 5 variations (walking, hand on hip, etc.)

### Footwear Mapping

```python
FOOTWEAR = {
    "dress": "heels",
    "pant": "white sneakers",
    "skirt": "heels",
    # ... customize per category
}
```

### Model Library

Add more models by:
1. Creating prompt in `model_generation_prompts.txt`
2. Running `generate_models.py`
3. Adding `MODEL_N_URL` to `.env`
4. Updating `config.py` range to `(1, N+1)`

## Troubleshooting

**"Classification failed" warnings:**
- Check `ANTHROPIC_API_KEY` is valid
- Verify Claude API credits
- Rate limit: 50+ images/min may throttle

**"Storage failed" errors:**
- Verify Cloudinary credentials
- Check `USE_CLOUDINARY=true`
- Ensure folder name matches `CLOUDINARY_FOLDER`

**Sheet not updating:**
- Verify service account has Editor access
- Check column names match `.env` config
- Ensure `credentials.json` exists

**Footwear color changing:**
- Prompts reinforced with "same footwear for all views"
- If persists, increase emphasis in `BASE_STUDIO`

## Tech Stack

- **Python 3.11+**
- **Fashn AI**: Product-to-model generation
- **Anthropic Claude**: Image classification
- **Google Sheets API**: Input/output data
- **Cloudinary**: Image storage & CDN
- **Flask**: Web dashboard

## License

Proprietary - All rights reserved

## Support

For issues or questions, contact the development team.