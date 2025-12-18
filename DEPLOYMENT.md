# Free Deployment Guide (No Credit Card Required)

## Prerequisites

You need accounts for these **FREE** services (no credit card required):

1. **Render** - Backend hosting
2. **Qdrant Cloud** - Vector database
3. **OpenAI** - API for embeddings/chat (requires payment, but you may have free credits)

---

## Step 1: Set Up Qdrant Cloud (Free Vector Database)

1. Go to https://cloud.qdrant.io/
2. Sign up with GitHub/Google (no credit card required)
3. Create a new cluster:
   - Name: `rag-chatbot`
   - Region: Choose closest to you
   - Plan: **Free** (1GB storage)
4. Once created, copy:
   - **Cluster URL** (e.g., `https://xxxxx.qdrant.io:6333`)
   - **API Key** (from cluster settings)

---

## Step 2: Deploy to Render (Free Backend Hosting)

### A. Push Your Code to GitHub

```bash
# In the backend directory
git init
git add .
git commit -m "Initial backend commit"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
git push -u origin main
```

### B. Deploy on Render

1. Go to https://render.com/
2. Sign up with GitHub (no credit card required)
3. Click **"New +"** → **"Blueprint"**
4. Connect your GitHub repository
5. Select the repository with your backend code
6. Render will detect `render.yaml` and show:
   - Web Service: `rag-chatbot-backend`
   - PostgreSQL Database: `rag-chatbot-db`
7. Click **"Apply"**

### C. Add Environment Variables

After deployment starts, go to your web service and add these secrets:

- `OPENAI_API_KEY` - Your OpenAI API key
- `QDRANT_URL` - From Step 1 (e.g., `https://xxxxx.qdrant.io:6333`)
- `QDRANT_API_KEY` - From Step 1

The PostgreSQL `DATABASE_URL` is automatically configured.

### D. Wait for Deployment

- First deployment takes ~5-10 minutes
- Check logs for any errors
- Once deployed, you'll get a URL like: `https://rag-chatbot-backend.onrender.com`

---

## Step 3: Test Your API

Visit your deployed URL:
- Health check: `https://YOUR_APP.onrender.com/health`
- API docs: `https://YOUR_APP.onrender.com/docs`

---

## Step 4: Update Frontend CORS

Add your Render URL to the CORS allowed origins in `src/main.py`:

```python
allow_origins=[
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://*.github.io",
    "https://*.vercel.app",
    "https://YOUR_APP.onrender.com",  # Add this
],
```

Then commit and push to trigger redeployment.

---

## Free Tier Limits

**Render Free Tier:**
- 750 hours/month compute time
- App sleeps after 15 minutes of inactivity
- Cold start time: ~30 seconds when waking up
- 512MB RAM

**Qdrant Cloud Free:**
- 1GB storage
- ~100k vectors (depending on size)
- Sufficient for educational chatbot

**PostgreSQL Free:**
- 1GB storage
- Shared CPU
- 90-day expiration (you'll get notified to extend)

---

## Keeping the App Awake (Optional)

Free Render services sleep after 15 minutes. To keep it awake:

1. Use a free uptime monitor:
   - **UptimeRobot** (https://uptimerobot.com/) - ping every 5 minutes
   - **Cron-job.org** (https://cron-job.org/) - schedule health checks

2. Add your Render health endpoint:
   - `https://YOUR_APP.onrender.com/health`

---

## Troubleshooting

**App won't start:**
- Check Render logs for errors
- Verify all environment variables are set
- Ensure Qdrant cluster URL includes port `:6333`

**Database connection errors:**
- Render auto-creates PostgreSQL - check if `DATABASE_URL` is set
- Try manual connection from Render dashboard

**OpenAI errors:**
- Verify API key is correct
- Check you have credits/billing enabled

---

## Next Steps

1. Set up Qdrant cluster ✓
2. Deploy to Render ✓
3. Add environment variables ✓
4. Test API endpoints ✓
5. Update frontend to use deployed backend URL
6. (Optional) Set up uptime monitoring

Your backend is now live and free!
