# Hugging Face Spaces - Quick Start Guide

Deploy your RAG Chatbot API to Hugging Face Spaces in under 15 minutes.

## TL;DR - Commands to Run

```bash
# 1. Navigate to backend
cd backend

# 2. Add Hugging Face remote (replace with your username and space name)
git remote add hf https://huggingface.co/spaces/YOUR_USERNAME/YOUR_SPACE_NAME

# 3. Commit and push
git add .
git commit -m "Deploy to Hugging Face Spaces"
git push hf main
```

Then configure secrets in Space settings, and you're live! 🚀

## Prerequisites Checklist

Before deploying, have these ready:

1. ✅ **Hugging Face account** - [Sign up](https://huggingface.co/join)
2. ✅ **Qdrant Cloud** cluster - [Get free cluster](https://cloud.qdrant.io/)
3. ✅ **PostgreSQL database** - [Neon](https://neon.tech/) or [Supabase](https://supabase.com/)
4. ✅ **OpenAI API key** - [Get key](https://platform.openai.com/api-keys)

## Step-by-Step Deployment

### 1️⃣ Create Hugging Face Space (2 min)

1. Go to: https://huggingface.co/new-space
2. Fill in:
   - **Space name**: `rag-chatbot-api`
   - **SDK**: Select **Docker** ⚠️ (NOT Gradio/Streamlit)
   - **Hardware**: CPU basic (free)
3. Click **Create Space**

### 2️⃣ Deploy Your Code (3 min)

```bash
# Navigate to backend directory
cd backend

# Add Hugging Face as a remote
git remote add hf https://huggingface.co/spaces/YOUR_USERNAME/YOUR_SPACE_NAME

# Push your code
git add .
git commit -m "Initial Hugging Face deployment"
git push hf main
```

You'll need:
- **Username**: Your HF username
- **Password**: Your HF access token (create at [settings/tokens](https://huggingface.co/settings/tokens))

### 3️⃣ Configure Secrets (5 min)

1. Go to your Space: `https://huggingface.co/spaces/YOUR_USERNAME/YOUR_SPACE_NAME`
2. Click **Settings** > **Repository secrets**
3. Add these 4 required secrets:

| Secret Name | Where to Get It | Example |
|-------------|-----------------|---------|
| `OPENAI_API_KEY` | [platform.openai.com/api-keys](https://platform.openai.com/api-keys) | `sk-proj-...` |
| `QDRANT_URL` | Qdrant Cloud dashboard | `https://abc.qdrant.io:6333` |
| `QDRANT_API_KEY` | Qdrant Cloud settings | `your-key` |
| `DATABASE_URL` | Neon/Supabase dashboard | `postgresql://user:pass@host/db?sslmode=require` |

### 4️⃣ Wait for Build (5 min)

1. Click **Logs** tab in your Space
2. Watch the build process
3. Wait for: `Application startup complete`
4. First build takes ~5-10 minutes

### 5️⃣ Test Your API (2 min)

**Health Check:**
```bash
curl https://YOUR_USERNAME-YOUR_SPACE_NAME.hf.space/health
```

**API Docs:**
```
https://YOUR_USERNAME-YOUR_SPACE_NAME.hf.space/docs
```

**Test Query:**
```bash
curl -X POST "https://YOUR_USERNAME-YOUR_SPACE_NAME.hf.space/v1/query" \
  -H "Content-Type: application/json" \
  -d '{"query": "What is machine learning?", "top_k": 5}'
```

## Getting External Services

### Qdrant Cloud (Vector Database)

```
1. Visit: https://cloud.qdrant.io/
2. Sign up (no credit card)
3. Create cluster (Free plan)
4. Copy URL and API key
```

**What you need:**
- Cluster URL (format: `https://xxxxx.qdrant.io:6333`)
- API Key

### PostgreSQL Database

Choose one:

**Option A: Neon** (Recommended)
```
1. Visit: https://neon.tech/
2. Create project
3. Copy connection string
```

**Option B: Supabase**
```
1. Visit: https://supabase.com/
2. Create project
3. Settings > Database > Copy connection string
```

**What you need:**
- Connection string (format: `postgresql://user:pass@host/db?sslmode=require`)

### OpenAI API

```
1. Visit: https://platform.openai.com/
2. Add payment method
3. Create API key: https://platform.openai.com/api-keys
4. Copy key (starts with sk-)
```

**What you need:**
- API Key (format: `sk-proj-...`)

## Troubleshooting

### Build Fails
- Check **Logs** tab for specific error
- Verify `Dockerfile` and `requirements.txt`

### Health Check Shows "unhealthy"
- Verify all 4 secrets are set correctly
- Check Qdrant URL includes `:6333` port
- Ensure database URL has `?sslmode=require`

### Space Sleeps
- Free Spaces sleep after 48h inactivity
- Use [UptimeRobot](https://uptimerobot.com/) to ping every 5 min
- Or upgrade to persistent hardware

### CORS Errors
- Frontend domain already whitelisted: `*.hf.space`
- For custom domain, add to `src/main.py` line 75

## Cost Breakdown

**Free Tier (What You Need):**
- Hugging Face Space: **$0** (free tier)
- Qdrant Cloud: **$0** (1GB free)
- PostgreSQL (Neon): **$0** (0.5GB free)
- OpenAI: **~$1-5/month** (usage-based)

**Total: $1-5/month** for moderate usage

## Update Your Deployment

```bash
# Make changes to code
# Then:
git add .
git commit -m "Update: description of changes"
git push hf main
```

Space rebuilds automatically.

## Next Steps

After deployment:

1. ✅ Test all API endpoints
2. 🔲 Update frontend to use new API URL
3. 🔲 Set up uptime monitoring
4. 🔲 Add content to vector database
5. 🔲 Monitor OpenAI usage/costs

## Useful Links

- **Your Space**: `https://huggingface.co/spaces/YOUR_USERNAME/YOUR_SPACE_NAME`
- **API Docs**: `https://YOUR_USERNAME-YOUR_SPACE_NAME.hf.space/docs`
- **HF Spaces Docs**: [huggingface.co/docs/hub/spaces](https://huggingface.co/docs/hub/spaces)
- **Support**: [discuss.huggingface.co](https://discuss.huggingface.co/)

## Full Documentation

For detailed deployment guide, see: `HUGGINGFACE_DEPLOY.md`
For deployment checklist, see: `DEPLOY_CHECKLIST.md`

---

**Questions?** Ask in your Space's discussion tab or HF forums.

**Ready to deploy?** Just run the commands above! 🚀
