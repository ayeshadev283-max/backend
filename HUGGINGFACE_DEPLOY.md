# Deploying RAG Chatbot API to Hugging Face Spaces

This guide walks you through deploying your FastAPI backend to Hugging Face Spaces using Docker.

## Why Hugging Face Spaces?

- **Free hosting** with generous compute resources (2 vCPU, 16GB RAM)
- **Automatic HTTPS** and custom domains
- **Built-in secrets management** for environment variables
- **Git-based deployment** with automatic rebuilds
- **Community features** (discussions, likes, etc.)
- **No credit card required** for free tier

## Prerequisites

1. **Hugging Face Account**: Sign up at [huggingface.co](https://huggingface.co/join)
2. **Git**: Installed on your machine
3. **External Services**:
   - Qdrant Cloud account ([cloud.qdrant.io](https://cloud.qdrant.io/))
   - PostgreSQL database (Neon, Supabase, or ElephantSQL)
   - OpenAI API key ([platform.openai.com](https://platform.openai.com/))

## Step 1: Set Up External Services

### 1.1 Qdrant Cloud (Vector Database)

1. Go to [cloud.qdrant.io](https://cloud.qdrant.io/)
2. Sign up with GitHub/Google (no credit card)
3. Create a new cluster:
   - **Name**: `rag-chatbot`
   - **Region**: Choose closest to you
   - **Plan**: Free (1GB storage)
4. Copy these values:
   - **Cluster URL**: `https://xxxxx.qdrant.io:6333` (note the `:6333` port)
   - **API Key**: From cluster settings

### 1.2 PostgreSQL Database

Choose one of these free options:

#### Option A: Neon (Recommended)
1. Go to [neon.tech](https://neon.tech/)
2. Sign up (no credit card)
3. Create a new project
4. Copy the **Connection String**:
   ```
   postgresql://user:password@ep-xxx.us-east-2.aws.neon.tech/neondb?sslmode=require
   ```

#### Option B: Supabase
1. Go to [supabase.com](https://supabase.com/)
2. Create a new project
3. Go to Settings > Database
4. Copy the **Connection String** (Postgres)

#### Option C: ElephantSQL
1. Go to [elephantsql.com](https://elephantsql.com/)
2. Create a new instance (Tiny Turtle - Free)
3. Copy the **URL** from instance details

### 1.3 OpenAI API Key

1. Go to [platform.openai.com](https://platform.openai.com/)
2. Sign up / Sign in
3. Add payment method (required, but you only pay for usage)
4. Go to [API keys page](https://platform.openai.com/api-keys)
5. Click **"Create new secret key"**
6. Copy and save the key (starts with `sk-`)

## Step 2: Create a Hugging Face Space

1. Go to [huggingface.co/new-space](https://huggingface.co/new-space)

2. Configure your Space:
   - **Owner**: Your username or organization
   - **Space name**: `rag-chatbot-api` (or your preferred name)
   - **License**: MIT
   - **Select SDK**: **Docker** ⚠️ IMPORTANT: Choose Docker, not Gradio/Streamlit
   - **Space hardware**: CPU basic (free tier)
   - **Visibility**: Public or Private

3. Click **"Create Space"**

## Step 3: Deploy Your Code

### 3.1 Navigate to Backend Directory

```bash
cd backend
```

### 3.2 Initialize Git (if not already initialized)

```bash
git init
```

### 3.3 Add Hugging Face Remote

Replace `YOUR_USERNAME` and `YOUR_SPACE_NAME` with your values:

```bash
git remote add hf https://huggingface.co/spaces/YOUR_USERNAME/YOUR_SPACE_NAME
```

Example:
```bash
git remote add hf https://huggingface.co/spaces/johndoe/rag-chatbot-api
```

### 3.4 Commit Your Code

```bash
git add .
git commit -m "Initial deployment to Hugging Face Spaces"
```

### 3.5 Push to Hugging Face

```bash
git push hf main
```

If you're on a different branch:
```bash
git push hf your-branch:main
```

**Note**: You'll be prompted for your Hugging Face credentials:
- **Username**: Your HF username
- **Password**: Your HF **Access Token** (not your account password)
  - Get your token at: [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens)
  - Create a **Write** token if you don't have one

## Step 4: Configure Environment Variables

1. Go to your Space page: `https://huggingface.co/spaces/YOUR_USERNAME/YOUR_SPACE_NAME`

2. Click on **Settings** (top right)

3. Scroll to **Repository secrets**

4. Add the following secrets one by one:

### Required Secrets

| Name | Value | Example |
|------|-------|---------|
| `OPENAI_API_KEY` | Your OpenAI API key | `sk-proj-xxx...` |
| `QDRANT_URL` | Qdrant cluster URL | `https://abc123.qdrant.io:6333` |
| `QDRANT_API_KEY` | Qdrant API key | `your-qdrant-key` |
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://user:pass@host/db` |

### Optional Secrets (with defaults)

| Name | Default | Description |
|------|---------|-------------|
| `OPENAI_EMBEDDING_MODEL` | `text-embedding-3-small` | Embedding model |
| `OPENAI_GENERATION_MODEL` | `gpt-4o-mini` | Chat model |
| `OPENAI_MAX_TOKENS` | `500` | Max response tokens |
| `QDRANT_COLLECTION_NAME` | `book_chunks_v1` | Collection name |
| `LOG_LEVEL` | `INFO` | Logging verbosity |

5. Click **"Add secret"** for each one

6. The Space will automatically rebuild when you add/change secrets

## Step 5: Monitor Deployment

1. Go to the **Logs** tab in your Space

2. Watch the build process:
   ```
   Building Docker image...
   Installing dependencies...
   Starting application...
   ```

3. Wait for the message:
   ```
   Application startup complete.
   Uvicorn running on http://0.0.0.0:8000
   ```

4. First deployment takes ~5-10 minutes

## Step 6: Test Your Deployment

Once the Space is running, test it:

### 6.1 Health Check

Visit:
```
https://YOUR_USERNAME-YOUR_SPACE_NAME.hf.space/health
```

Expected response:
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

### 6.2 API Documentation

Visit:
```
https://YOUR_USERNAME-YOUR_SPACE_NAME.hf.space/docs
```

You should see the interactive Swagger UI.

### 6.3 Test Query Endpoint

```bash
curl -X POST "https://YOUR_USERNAME-YOUR_SPACE_NAME.hf.space/v1/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is machine learning?",
    "top_k": 5
  }'
```

## Step 7: Update Frontend Configuration

Update your frontend to use the Hugging Face Space URL:

```javascript
// In your Docusaurus site config or API client
const API_BASE_URL = "https://YOUR_USERNAME-YOUR_SPACE_NAME.hf.space"
```

## Troubleshooting

### Space Build Fails

**Check logs for errors:**
- Missing dependencies: Verify `requirements.txt`
- Python version mismatch: Ensure `runtime.txt` has correct version

**Common fixes:**
```bash
# Verify Dockerfile syntax
docker build -t test-backend .

# Test locally first
docker run -p 8000:8000 --env-file .env test-backend
```

### Space Running but Health Check Fails

**Database Connection Issues:**
- Verify `DATABASE_URL` is correct
- Check database service is accessible from internet
- Ensure SSL mode is configured: `?sslmode=require`

**Qdrant Connection Issues:**
- Verify `QDRANT_URL` includes port `:6333`
- Check API key is correct
- Ensure Qdrant cluster is not paused

**OpenAI Issues:**
- Verify API key starts with `sk-`
- Check billing is enabled
- Verify you have credits

### Space Sleeps After Inactivity

Free Spaces sleep after 48 hours of inactivity.

**To keep it awake:**
1. Use a free uptime monitor:
   - [UptimeRobot](https://uptimerobot.com/) - ping every 5 min
   - [Cron-job.org](https://cron-job.org/) - scheduled checks

2. Set up monitoring:
   - URL: `https://YOUR_SPACE.hf.space/health`
   - Interval: 5-15 minutes

**Or upgrade to persistent hardware** (paid tier)

### CORS Errors

If your frontend gets CORS errors:

1. Verify frontend domain is in allowed origins (`src/main.py:70-75`)
2. Add your domain:
   ```python
   allow_origins=[
       ...
       "https://your-frontend.com",
   ]
   ```
3. Commit and push to redeploy

### Rate Limiting

If you hit OpenAI rate limits:

1. Upgrade OpenAI tier
2. Implement caching
3. Reduce `top_k` retrieval
4. Add request throttling

## Updating Your Deployment

### Push New Changes

```bash
# Make your changes
git add .
git commit -m "Update: description of changes"
git push hf main
```

The Space will automatically rebuild.

### Update Environment Variables

1. Go to Space Settings > Repository secrets
2. Update the secret value
3. Space will automatically restart

### Rollback to Previous Version

```bash
# Find commit hash
git log

# Reset to previous commit
git reset --hard COMMIT_HASH

# Force push
git push -f hf main
```

## Performance Optimization

### Enable Caching

Add Redis or in-memory caching for:
- Frequently asked questions
- Embedding results
- Database queries

### Optimize Vector Search

- Reduce `top_k` from 5 to 3
- Increase `SIMILARITY_THRESHOLD`
- Use smaller embedding models

### Upgrade Space Hardware

For better performance:
1. Go to Space Settings
2. Select **Space hardware**
3. Choose:
   - **CPU Upgrade** ($0.03/hour) - 8 vCPU, 32GB RAM
   - **GPU** ($0.60/hour) - For faster embeddings

## Monitoring and Analytics

### Built-in Metrics

Hugging Face provides:
- Request counts
- Error rates
- Response times

Access via Space settings > **Analytics**

### Custom Logging

View application logs:
1. Go to your Space
2. Click **Logs** tab
3. Filter by:
   - Build logs
   - Container logs
   - Application logs

### External Monitoring

Integrate with:
- **Sentry** - Error tracking
- **LogTail** - Log aggregation
- **Better Stack** - Full observability

## Cost Considerations

### Free Tier

- **Compute**: Free (with sleep after inactivity)
- **Bandwidth**: Unlimited
- **Storage**: Limited to Docker image size

### Paid Tier (Optional)

- **Persistent hardware**: $0.03-$0.60/hour
- **No sleep**: Always-on availability
- **Better performance**: More CPU/RAM/GPU

### External Services

- **Qdrant Cloud Free**: 1GB (enough for ~100k vectors)
- **PostgreSQL Free**: 0.5-1GB
- **OpenAI**: Pay per token (~$0.10 per 1M tokens for gpt-4o-mini)

**Estimated monthly cost**: $5-20 for moderate usage

## Best Practices

1. **Use environment variables** for all secrets
2. **Monitor logs** regularly for errors
3. **Set up health checks** with uptime monitors
4. **Version your API** (`/v1/query` pattern)
5. **Implement rate limiting** to control costs
6. **Cache responses** for common queries
7. **Use semantic versioning** for releases
8. **Test locally** before deploying
9. **Document API changes** in README
10. **Monitor OpenAI usage** to avoid unexpected bills

## Next Steps

1. ✅ Deploy to Hugging Face Spaces
2. ✅ Configure environment variables
3. ✅ Test all endpoints
4. 🔲 Update frontend to use new API URL
5. 🔲 Set up uptime monitoring
6. 🔲 Configure custom domain (optional)
7. 🔲 Add API authentication (recommended for production)
8. 🔲 Implement caching layer
9. 🔲 Set up error monitoring
10. 🔲 Create usage analytics dashboard

## Getting Help

- **Hugging Face Docs**: [huggingface.co/docs/hub/spaces](https://huggingface.co/docs/hub/spaces)
- **Community Forums**: [discuss.huggingface.co](https://discuss.huggingface.co/)
- **Discord**: [hf.co/join/discord](https://hf.co/join/discord)
- **Space Discussions**: Use the discussions tab on your Space

## Example Deployment

See a working example:
- Space: [huggingface.co/spaces/example/rag-chatbot](https://huggingface.co/spaces)
- API: [example-rag-chatbot.hf.space/docs](https://hf.space/docs)

---

**Deployment complete!** 🚀 Your RAG chatbot API is now live on Hugging Face Spaces.
