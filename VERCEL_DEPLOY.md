# Deploy Backend to Vercel (100% Free - No Card)

## Prerequisites (All Free, No Card)

1. **Qdrant Cloud** - Vector database
2. **Neon** - PostgreSQL database
3. **Vercel** - Backend hosting
4. **OpenAI API** - You need an API key (requires payment)

---

## Step 1: Setup Qdrant (2 minutes)

1. Go to https://cloud.qdrant.io/
2. Click **Sign Up** → Use GitHub (FREE)
3. Create new cluster:
   - Name: `rag-chatbot`
   - Plan: **Free** (1GB)
4. Copy:
   - **Cluster URL**: `https://xxxxx.qdrant.io:6333`
   - **API Key**: From cluster settings

---

## Step 2: Setup Neon PostgreSQL (2 minutes)

1. Go to https://neon.tech/
2. Click **Sign Up** → Use GitHub (FREE)
3. Create new project:
   - Name: `chatbot-db`
   - Region: Choose closest
4. Copy **Connection String**:
   ```
   postgresql://user:password@ep-xxx.neon.tech/chatbot_db?sslmode=require
   ```

---

## Step 3: Deploy to Vercel (3 minutes)

### A. Push Code to GitHub

```bash
cd backend
git add vercel.json api/
git commit -m "Add Vercel serverless config"
git push origin main
```

### B. Deploy on Vercel

1. Go to https://vercel.com/
2. Click **Sign Up** → Use GitHub (FREE)
3. Click **"Add New Project"**
4. Select your backend repository: `ayeshadev283-max/backend`
5. Configure:
   - **Framework Preset**: Other
   - **Root Directory**: Leave as `./`
6. Click **"Deploy"**

### C. Add Environment Variables

After deployment starts, go to **Settings** → **Environment Variables**:

Add these variables:

```
OPENAI_API_KEY=sk-your-key-here
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
OPENAI_GENERATION_MODEL=gpt-4o-mini
OPENAI_MAX_TOKENS=500
OPENAI_TEMPERATURE=0.0

QDRANT_URL=https://xxxxx.qdrant.io:6333
QDRANT_API_KEY=your-qdrant-key
QDRANT_COLLECTION_NAME=book_chunks_v1

DATABASE_URL=postgresql://user:password@ep-xxx.neon.tech/chatbot_db?sslmode=require

API_HOST=0.0.0.0
API_PORT=8000
LOG_LEVEL=INFO

CHUNK_SIZE=500
CHUNK_OVERLAP=50
TOP_K_RETRIEVAL=5
SIMILARITY_THRESHOLD=0.7
RATE_LIMIT_PER_HOUR=60

DEV_MODE=false
```

Click **"Save"** - Vercel will redeploy automatically.

---

## Step 4: Get Your Backend URL

After deployment completes (2-3 minutes):
- Your URL: `https://YOUR_PROJECT.vercel.app`
- Test health: `https://YOUR_PROJECT.vercel.app/health`

---

## Step 5: Update Frontend

Update `src/hooks/useChatbot.ts` with your Vercel URL:

```typescript
const API_BASE_URL = process.env.NODE_ENV === 'production'
  ? 'https://YOUR_PROJECT.vercel.app'  // Your Vercel URL
  : 'http://localhost:8000';
```

Then rebuild and deploy frontend.

---

## Free Tier Limits

**Vercel Free:**
- 100GB bandwidth/month
- Serverless function executions
- No credit card required

**Qdrant Cloud Free:**
- 1GB storage
- ~100k vectors
- No expiration

**Neon Free:**
- 0.5GB storage
- 1 project
- No expiration

---

## Troubleshooting

**Vercel deployment fails:**
- Check build logs in Vercel dashboard
- Ensure all dependencies in `requirements.txt`

**Database connection errors:**
- Verify DATABASE_URL is correct
- Check Neon project is active

**Qdrant errors:**
- Ensure URL includes port `:6333`
- Verify API key is correct

---

## Important Notes

1. **OpenAI API** still requires payment (but uses your API key)
2. All other services are 100% free
3. No credit card needed for Vercel, Qdrant, or Neon
4. Serverless functions have cold start (~1-2s first request)

Your backend is now live for FREE!
