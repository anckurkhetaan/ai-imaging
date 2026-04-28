# Deployment Guide - Render

## Prerequisites

1. GitHub repo pushed: https://github.com/anckurkhetaan/ai-imaging
2. Render account: https://render.com (sign up with GitHub)
3. Google Service Account credentials JSON file content (you'll paste this)

## Steps

### 1. Create New Web Service

1. Go to https://dashboard.render.com
2. Click **New +** → **Web Service**
3. Connect your GitHub account (if not already)
4. Select repository: `anckurkhetaan/ai-imaging`
5. Click **Connect**

### 2. Configure Service

**Basic Settings:**
- Name: `fashn-ai-pipeline`
- Region: Choose closest to your users
- Branch: `main`
- Root Directory: leave blank (or set to `fashn_pipeline` if you organized repo differently)
- Runtime: `Python 3`
- Build Command: `pip install -r requirements.txt`
- Start Command: `gunicorn app:app`

**Instance Type:**
- Free tier for testing
- Starter ($7/month) for production (recommended - keeps running)

### 3. Add Environment Variables

Click **Environment** tab, add these:

**Required:**
```
FASHN_API_KEY=your_fashn_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here
GSHEET_SPREADSHEET_ID=your_spreadsheet_id_here
CLOUDINARY_CLOUD_NAME=your_cloudinary_cloud_name
CLOUDINARY_API_KEY=your_cloudinary_api_key
CLOUDINARY_API_SECRET=your_cloudinary_api_secret
USE_CLOUDINARY=true
CLOUDINARY_FOLDER=BrownButter
```

**Model Library URLs (all 12):**
```
MODEL_1_URL=https://res.cloudinary.com/.../model_1.jpg
MODEL_2_URL=https://res.cloudinary.com/.../model_2.jpg
MODEL_3_URL=https://res.cloudinary.com/.../model_3.jpg
MODEL_4_URL=https://res.cloudinary.com/.../model_4.jpg
MODEL_5_URL=https://res.cloudinary.com/.../model_5.jpg
MODEL_6_URL=https://res.cloudinary.com/.../model_6.jpg
MODEL_7_URL=https://res.cloudinary.com/.../model_7.jpg
MODEL_8_URL=https://res.cloudinary.com/.../model_8.jpg
MODEL_9_URL=https://res.cloudinary.com/.../model_9.jpg
MODEL_10_URL=https://res.cloudinary.com/.../model_10.jpg
MODEL_11_URL=https://res.cloudinary.com/.../model_11.jpg
MODEL_12_URL=https://res.cloudinary.com/.../model_12.jpg
```

**Google Sheets Config:**
```
GSHEET_SHEET_NAME=ImageBank
COL_PRODUCT_ID=New_Product_Id
COL_CATEGORY=Sub_Category_Name
COL_IMAGE_LINKS=Product_Image_Main_URL,Second_Image_Ifany,Third_Image_Ifany
COL_OUTPUT_IMAGES=output_image_1,output_image_2,output_image_3
GSHEET_CREDENTIALS_PATH=credentials.json
```

**Optional (use defaults if not set):**
```
FASHN_BASE_URL=https://api.fashn.ai/v1
FASHN_POLL_INTERVAL_SEC=5
FASHN_POLL_TIMEOUT_SEC=120
FASHN_OUTPUT_FORMAT=jpeg
CLAUDE_VISION_MODEL=claude-haiku-4-5-20251001
OUTPUT_DIR=outputs
```

### 4. Add Google Credentials as Secret File

**CRITICAL:** Render needs your `credentials.json` content as an environment variable.

1. In Render Environment tab, add new variable:
   - Key: `GOOGLE_CREDENTIALS_JSON`
   - Value: Paste your **entire** `credentials.json` content (the full JSON)

2. Update `config.py` to handle this (already done if using latest code):
   ```python
   # This reads from env var or file
   ```

**Alternative:** Use Render Secret Files (recommended for JSON):
1. In Render dashboard → your service → Environment
2. Click **Secret Files**
3. Add file:
   - Filename: `credentials.json`
   - Contents: Paste your full credentials.json content
4. This creates the file at `/etc/secrets/credentials.json`
5. Update `.env` var: `GSHEET_CREDENTIALS_PATH=/etc/secrets/credentials.json`

### 5. Deploy

1. Click **Create Web Service**
2. Render will:
   - Clone your repo
   - Install dependencies
   - Start gunicorn server
3. Watch build logs for errors
4. Once deployed, you'll get a URL: `https://fashn-ai-pipeline.onrender.com`

### 6. Test

1. Visit your Render URL
2. Click **▶ Start Pipeline**
3. Watch products process in real-time!

## Troubleshooting

**"ModuleNotFoundError":**
- Check `requirements.txt` has all dependencies
- Rebuild service

**"credentials.json not found":**
- Verify Secret File path matches `GSHEET_CREDENTIALS_PATH`
- Or use environment variable approach

**"Pipeline idle immediately":**
- Check Google Sheets has unprocessed rows
- Verify all env vars are set correctly

**Slow performance:**
- Upgrade from Free to Starter tier
- Free tier spins down after 15 min inactivity

**Logs not showing:**
- Check browser console for errors
- Verify `/api/status` endpoint works

## Production Notes

**Free Tier Limitations:**
- Spins down after 15 minutes of inactivity
- 750 hours/month free
- Cold starts take 30-60 seconds

**Starter Tier Benefits ($7/month):**
- Always running (no spin-down)
- Faster performance
- Better for production use

## Monitoring

- View logs: Render Dashboard → Logs tab
- Check metrics: Render Dashboard → Metrics tab
- Set up alerts: Render Dashboard → Notifications

## Updating

Push changes to GitHub:
```bash
git add .
git commit -m "Update pipeline"
git push
```

Render auto-deploys on push to `main` branch.

## Security

- Never commit `.env` or `credentials.json`
- All secrets in Render Environment Variables
- Use Secret Files for JSON credentials
- Enable HTTPS (automatic on Render)
