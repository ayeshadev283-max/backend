# Hugging Face Deployment Checklist

Use this checklist to ensure a smooth deployment of your RAG Chatbot API to Hugging Face Spaces.

## Pre-Deployment

### External Services Setup

- [ ] **Qdrant Cloud**
  - [ ] Account created at [cloud.qdrant.io](https://cloud.qdrant.io/)
  - [ ] Free cluster created
  - [ ] Cluster URL copied (format: `https://xxxxx.qdrant.io:6333`)
  - [ ] API key copied
  - [ ] Collection will be auto-created on first run

- [ ] **PostgreSQL Database**
  - [ ] Database service chosen (Neon/Supabase/ElephantSQL)
  - [ ] Account created
  - [ ] Database instance created
  - [ ] Connection string copied (format: `postgresql://user:pass@host/db?sslmode=require`)

- [ ] **OpenAI API**
  - [ ] Account created at [platform.openai.com](https://platform.openai.com/)
  - [ ] Billing/payment method added
  - [ ] API key generated (starts with `sk-`)
  - [ ] API key copied and saved securely

### Code Preparation

- [ ] Backend code is ready in `backend/` directory
- [ ] `README.md` exists with Hugging Face front matter
- [ ] `Dockerfile` is present and correct
- [ ] `requirements.txt` has all dependencies
- [ ] `.dockerignore` excludes unnecessary files
- [ ] CORS settings include `https://*.hf.space`

## Deployment Steps

### 1. Create Hugging Face Space

- [ ] Go to [huggingface.co/new-space](https://huggingface.co/new-space)
- [ ] Choose a Space name
- [ ] Select **Docker** as SDK (CRITICAL!)
- [ ] Choose CPU basic (free)
- [ ] Set visibility (Public/Private)
- [ ] Click "Create Space"
- [ ] Note your Space URL: `https://huggingface.co/spaces/USERNAME/SPACE_NAME`

### 2. Deploy Code

- [ ] Navigate to backend directory: `cd backend`
- [ ] Initialize git (if needed): `git init`
- [ ] Add Hugging Face remote:
  ```bash
  git remote add hf https://huggingface.co/spaces/USERNAME/SPACE_NAME
  ```
- [ ] Commit changes: `git commit -m "Initial HF deployment"`
- [ ] Push to Hugging Face: `git push hf main`
- [ ] Enter HF credentials when prompted:
  - Username: Your HF username
  - Password: Your HF Access Token (from [settings/tokens](https://huggingface.co/settings/tokens))

### 3. Configure Secrets

Go to Space Settings > Repository secrets and add:

- [ ] `OPENAI_API_KEY` = `sk-...`
- [ ] `QDRANT_URL` = `https://xxxxx.qdrant.io:6333`
- [ ] `QDRANT_API_KEY` = `your-qdrant-key`
- [ ] `DATABASE_URL` = `postgresql://user:pass@host/db?sslmode=require`

Optional secrets:
- [ ] `OPENAI_EMBEDDING_MODEL` (default: `text-embedding-3-small`)
- [ ] `OPENAI_GENERATION_MODEL` (default: `gpt-4o-mini`)
- [ ] `QDRANT_COLLECTION_NAME` (default: `book_chunks_v1`)
- [ ] `LOG_LEVEL` (default: `INFO`)

### 4. Monitor Build

- [ ] Go to Space Logs tab
- [ ] Watch Docker build process
- [ ] Wait for "Application startup complete" message
- [ ] Check for any error messages
- [ ] Estimated time: 5-10 minutes

## Post-Deployment Testing

### Health Checks

- [ ] Visit health endpoint:
  ```
  https://USERNAME-SPACE_NAME.hf.space/health
  ```
- [ ] Verify response shows `"status": "healthy"`
- [ ] Check all services are healthy:
  - [ ] `database: "healthy"`
  - [ ] `vector_db: "healthy"`
  - [ ] `openai_api: "healthy"`

### API Documentation

- [ ] Visit API docs:
  ```
  https://USERNAME-SPACE_NAME.hf.space/docs
  ```
- [ ] Verify Swagger UI loads
- [ ] Check all endpoints are listed
- [ ] Test `/health` endpoint from UI

### Functional Testing

- [ ] Test query endpoint with curl:
  ```bash
  curl -X POST "https://USERNAME-SPACE_NAME.hf.space/v1/query" \
    -H "Content-Type: application/json" \
    -d '{"query": "What is machine learning?", "top_k": 5}'
  ```
- [ ] Verify response contains:
  - [ ] `answer` field with text
  - [ ] `sources` array with relevant chunks
  - [ ] `metadata` with timestamps
- [ ] Test with different queries
- [ ] Verify response times are acceptable

## Frontend Integration

- [ ] Update frontend API base URL to:
  ```
  https://USERNAME-SPACE_NAME.hf.space
  ```
- [ ] Test chatbot from frontend
- [ ] Verify no CORS errors in browser console
- [ ] Test multiple queries
- [ ] Check response formatting

## Monitoring Setup (Optional but Recommended)

### Uptime Monitoring

- [ ] Sign up for uptime monitor:
  - Option 1: [UptimeRobot](https://uptimerobot.com/)
  - Option 2: [Cron-job.org](https://cron-job.org/)
- [ ] Add monitor for health endpoint
- [ ] Set check interval to 5-15 minutes
- [ ] Configure alerts (email/SMS)

### Error Tracking

- [ ] Set up error monitoring (optional):
  - Sentry
  - LogTail
  - Better Stack
- [ ] Configure alert thresholds
- [ ] Test error notifications

## Documentation

- [ ] Update main README with:
  - [ ] Live API URL
  - [ ] Example API calls
  - [ ] Environment variables used
- [ ] Update frontend docs with new backend URL
- [ ] Document any deployment-specific configuration
- [ ] Add troubleshooting section for common issues

## Security & Best Practices

- [ ] Never commit `.env` file
- [ ] Use HF secrets for all sensitive data
- [ ] Enable API authentication (if needed)
- [ ] Set up rate limiting (if needed)
- [ ] Review CORS settings
- [ ] Enable HTTPS only (default on HF)
- [ ] Monitor OpenAI usage to control costs

## Cost Monitoring

- [ ] Check OpenAI usage dashboard
- [ ] Monitor Qdrant storage usage
- [ ] Monitor PostgreSQL storage usage
- [ ] Set up billing alerts (OpenAI)
- [ ] Estimate monthly costs based on traffic

## Troubleshooting Common Issues

If deployment fails, check:

- [ ] **Build fails**
  - [ ] Verify Dockerfile syntax
  - [ ] Check requirements.txt for invalid packages
  - [ ] Review build logs for specific errors

- [ ] **Database connection fails**
  - [ ] Verify DATABASE_URL format is correct
  - [ ] Check database is accessible from internet
  - [ ] Ensure SSL mode is configured

- [ ] **Qdrant connection fails**
  - [ ] Verify URL includes `:6333` port
  - [ ] Check API key is correct
  - [ ] Ensure cluster is not paused

- [ ] **OpenAI errors**
  - [ ] Verify API key is valid
  - [ ] Check billing is enabled
  - [ ] Verify you have credits

- [ ] **CORS errors**
  - [ ] Add frontend domain to `src/main.py`
  - [ ] Commit and redeploy

## Maintenance Tasks

### Weekly
- [ ] Check error logs
- [ ] Monitor response times
- [ ] Review OpenAI costs

### Monthly
- [ ] Update dependencies
- [ ] Review and optimize queries
- [ ] Check database size
- [ ] Extend free database if needed (some expire after 90 days)

### As Needed
- [ ] Deploy new features
- [ ] Fix bugs
- [ ] Scale up hardware if needed

## Rollback Plan

If something goes wrong:

1. [ ] Find last working commit: `git log`
2. [ ] Reset to that commit: `git reset --hard COMMIT_HASH`
3. [ ] Force push: `git push -f hf main`
4. [ ] Monitor build and verify health

## Success Criteria

Deployment is successful when:

- [x] Space is running without errors
- [x] Health endpoint returns all services healthy
- [x] API docs are accessible
- [x] Query endpoint returns valid responses
- [x] Frontend can communicate with backend
- [x] No CORS errors
- [x] Response times are acceptable (< 3s)
- [x] Uptime monitoring is configured
- [x] Documentation is updated

## Next Steps After Deployment

- [ ] Add more content to vector database
- [ ] Implement caching for better performance
- [ ] Add analytics/metrics tracking
- [ ] Implement feedback mechanism
- [ ] Add API authentication
- [ ] Set up CI/CD pipeline
- [ ] Create usage documentation for end users
- [ ] Plan for scaling (if needed)

---

## Quick Reference

**Space URL**: `https://USERNAME-SPACE_NAME.hf.space`

**Useful Commands**:
```bash
# Deploy updates
git add .
git commit -m "Update: description"
git push hf main

# Check status
curl https://USERNAME-SPACE_NAME.hf.space/health

# Test query
curl -X POST "https://USERNAME-SPACE_NAME.hf.space/v1/query" \
  -H "Content-Type: application/json" \
  -d '{"query": "test", "top_k": 3}'
```

**Support**:
- HF Docs: [huggingface.co/docs/hub/spaces](https://huggingface.co/docs/hub/spaces)
- Discord: [hf.co/join/discord](https://hf.co/join/discord)
- Forums: [discuss.huggingface.co](https://discuss.huggingface.co/)

---

**Status**: ✅ Ready to deploy | 🚀 Deploying | ✅ Deployed | 🔧 Troubleshooting

**Deployment Date**: _____________

**Deployed By**: _____________

**Space URL**: _____________
