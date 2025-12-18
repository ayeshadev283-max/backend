# Deploy to Your Hugging Face Space NOW

## Your Space Details

- **Space URL**: https://huggingface.co/spaces/ayeshassdev/aibook
- **API URL** (after deployment): https://ayeshassdev-aibook.hf.space
- **SDK**: Docker ✅
- **Port**: 7860 ✅

---

## 🚀 Deployment Commands - Run These Now

### Step 1: Add Hugging Face Remote

```bash
cd backend
git remote add hf https://huggingface.co/spaces/ayeshassdev/aibook
```

### Step 2: Commit Latest Changes

```bash
git add .
git commit -m "Deploy RAG Chatbot API to Hugging Face Spaces"
```

### Step 3: Push to Hugging Face

```bash
git push hf main
```

**When prompted:**
- **Username**: `ayeshassdev`
- **Password**: Your Hugging Face **Access Token**
  - Get it here: https://huggingface.co/settings/tokens
  - Click "New token" → Select "Write" access → Copy token

---

## ⚙️ Configure Environment Secrets

After pushing, go to your Space settings and add these secrets:

**Settings URL**: https://huggingface.co/spaces/ayeshassdev/aibook/settings

Click **"Repository secrets"** and add:

### Required Secrets (4)

| Secret Name | Value | Where to Get |
|-------------|-------|--------------|
| `OPENAI_API_KEY` | `sk-proj-...` | https://platform.openai.com/api-keys |
| `QDRANT_URL` | `https://xxx.qdrant.io:6333` | https://cloud.qdrant.io/ |
| `QDRANT_API_KEY` | Your Qdrant API key | Qdrant cluster settings |
| `DATABASE_URL` | `postgresql://user:pass@host/db?sslmode=require` | Neon or Supabase dashboard |

### Optional Secrets

| Secret Name | Default Value | Description |
|-------------|---------------|-------------|
| `OPENAI_EMBEDDING_MODEL` | `text-embedding-3-small` | Embedding model to use |
| `OPENAI_GENERATION_MODEL` | `gpt-4o-mini` | Chat completion model |
| `QDRANT_COLLECTION_NAME` | `book_chunks_v1` | Vector collection name |
| `LOG_LEVEL` | `INFO` | Logging verbosity |

---

## 📊 Monitor Deployment

1. **Go to Logs**: https://huggingface.co/spaces/ayeshassdev/aibook?logs=container

2. **Watch for these messages:**
   ```
   Building Docker image...
   ✓ Dependencies installed
   ✓ Application copied
   Starting application...
   INFO: Application startup complete
   INFO: Uvicorn running on http://0.0.0.0:7860
   ```

3. **First deployment takes**: 5-10 minutes

---

## ✅ Test Your Deployment

### Health Check

```bash
curl https://ayeshassdev-aibook.hf.space/health
```

**Expected response:**
```json
{
  "status": "healthy",
  "services": {
    "database": "healthy",
    "vector_db": "healthy",
    "openai_api": "healthy"
  }
}
```

### API Documentation

Visit: **https://ayeshassdev-aibook.hf.space/docs**

### Test Query

```bash
curl -X POST "https://ayeshassdev-aibook.hf.space/v1/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is artificial intelligence?",
    "top_k": 5
  }'
```

---

## 🔧 Setup External Services (If Not Done)

### 1. Qdrant Cloud (Vector Database)

```
1. Visit: https://cloud.qdrant.io/
2. Sign up (free, no credit card)
3. Create cluster → Free plan
4. Copy:
   - Cluster URL (must include :6333)
   - API Key
```

### 2. Neon PostgreSQL (Database)

```
1. Visit: https://neon.tech/
2. Sign up (free)
3. Create project
4. Copy connection string from dashboard
   Format: postgresql://user:pass@host/db?sslmode=require
```

### 3. OpenAI API Key

```
1. Visit: https://platform.openai.com/
2. Add payment method (pay-as-you-go)
3. Go to: https://platform.openai.com/api-keys
4. Create new secret key
5. Copy key (starts with sk-)
```

---

## 🎯 Quick Troubleshooting

### Build Fails
- Check **Logs** tab in Space
- Verify Dockerfile syntax
- Ensure requirements.txt is valid

### Health Check Returns "unhealthy"
- Verify all 4 secrets are set in Space settings
- Check Qdrant URL has `:6333` at the end
- Ensure DATABASE_URL has `?sslmode=require`
- Verify OpenAI API key is correct

### Can't Push to Hugging Face
- Make sure you're using Access Token, not password
- Token must have "Write" permission
- Create token at: https://huggingface.co/settings/tokens

### CORS Errors from Frontend
- Already configured for `*.hf.space` domains
- Frontend should use: `https://ayeshassdev-aibook.hf.space`

---

## 📱 Update Your Frontend

After deployment, update your frontend to use:

```javascript
// API base URL
const API_BASE_URL = "https://ayeshassdev-aibook.hf.space"

// Example query
fetch(`${API_BASE_URL}/v1/query`, {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    query: "What is machine learning?",
    top_k: 5
  })
})
```

---

## 🔄 Deploy Updates Later

```bash
cd backend
git add .
git commit -m "Update: description of changes"
git push hf main
```

Space rebuilds automatically on every push.

---

## 📞 Get Help

- **HF Docs**: https://huggingface.co/docs/hub/spaces
- **Discord**: https://hf.co/join/discord
- **Forums**: https://discuss.huggingface.co/

---

## ✨ Your URLs

After deployment, bookmark these:

- **Space Dashboard**: https://huggingface.co/spaces/ayeshassdev/aibook
- **API Base**: https://ayeshassdev-aibook.hf.space
- **API Docs**: https://ayeshassdev-aibook.hf.space/docs
- **Health Check**: https://ayeshassdev-aibook.hf.space/health

---

**Ready? Run the commands above!** 🚀

**Status**: 🔲 Not Deployed | 🚀 Deploying | ✅ Live
