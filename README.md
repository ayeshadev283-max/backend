---
title: RAG Chatbot API
emoji: 🤖
colorFrom: blue
colorTo: green
sdk: docker
pinned: false
license: mit
app_port: 7860
---

# RAG Chatbot API for Educational Resources

A FastAPI-based Retrieval-Augmented Generation (RAG) chatbot backend designed for educational content. This API uses vector search and LLMs to provide intelligent responses based on indexed educational materials.

## Features

- **FastAPI** backend with automatic OpenAPI documentation
- **Vector Search** using Qdrant for semantic retrieval
- **PostgreSQL** for persistent storage
- **OpenAI Integration** for embeddings and chat completions
- **CORS Support** for frontend integration
- **Health Monitoring** with detailed service status

## Live API Documentation

Once deployed, visit:
- **API Docs**: `https://your-space-name.hf.space/docs`
- **Health Check**: `https://your-space-name.hf.space/health`

## Environment Variables

This Space requires the following environment variables to be configured in the Space settings:

### Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key for embeddings and chat | `sk-...` |
| `QDRANT_URL` | Qdrant Cloud cluster URL | `https://xxx.qdrant.io:6333` |
| `QDRANT_API_KEY` | Qdrant API key | `your-key` |
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://user:pass@host/db` |

### Optional Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_EMBEDDING_MODEL` | Embedding model | `text-embedding-3-small` |
| `OPENAI_GENERATION_MODEL` | Chat model | `gpt-4o-mini` |
| `OPENAI_MAX_TOKENS` | Max response tokens | `500` |
| `OPENAI_TEMPERATURE` | Model temperature | `0.0` |
| `QDRANT_COLLECTION_NAME` | Qdrant collection name | `book_chunks_v1` |
| `LOG_LEVEL` | Logging level | `INFO` |
| `TOP_K_RETRIEVAL` | Number of chunks to retrieve | `5` |
| `SIMILARITY_THRESHOLD` | Minimum similarity score | `0.7` |

## Setup Instructions

### 1. Deploy to Hugging Face Spaces

1. **Create a new Space**:
   - Go to [Hugging Face Spaces](https://huggingface.co/new-space)
   - Select **Docker** as the SDK
   - Choose a name for your Space

2. **Upload your code**:
   ```bash
   cd backend
   git init
   git add .
   git commit -m "Initial commit"
   git remote add space https://huggingface.co/spaces/YOUR_USERNAME/YOUR_SPACE_NAME
   git push --force space main
   ```

3. **Configure Secrets**:
   - Go to your Space settings
   - Navigate to **Repository secrets**
   - Add all required environment variables listed above

### 2. Set Up External Services

#### Qdrant Cloud (Free)
1. Sign up at [cloud.qdrant.io](https://cloud.qdrant.io/)
2. Create a new cluster (Free tier: 1GB)
3. Copy the **Cluster URL** and **API Key**

#### PostgreSQL Database
Choose one of these free options:
- **Neon** ([neon.tech](https://neon.tech/)) - Free tier: 0.5GB
- **Supabase** ([supabase.com](https://supabase.com/)) - Free tier: 500MB
- **ElephantSQL** ([elephantsql.com](https://elephantsql.com/)) - Free tier: 20MB

#### OpenAI API
1. Create account at [platform.openai.com](https://platform.openai.com/)
2. Add payment method (pay-as-you-go)
3. Generate API key from [API keys page](https://platform.openai.com/api-keys)

### 3. Test Your Deployment

Once deployed, test the endpoints:

```bash
# Health check
curl https://YOUR_SPACE_NAME.hf.space/health

# API documentation
open https://YOUR_SPACE_NAME.hf.space/docs
```

## API Endpoints

### Health Check
```bash
GET /health
```

Returns service health status including database connections.

### Query
```bash
POST /v1/query
Content-Type: application/json

{
  "query": "What is machine learning?",
  "top_k": 5
}
```

Returns AI-generated response based on indexed content.

### API Documentation
```bash
GET /docs
```

Interactive Swagger UI for exploring all endpoints.

## Development

### Local Development

1. **Clone the repository**:
   ```bash
   git clone https://huggingface.co/spaces/YOUR_USERNAME/YOUR_SPACE_NAME
   cd YOUR_SPACE_NAME
   ```

2. **Set up environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your credentials
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Run locally**:
   ```bash
   uvicorn src.main:app --reload
   ```

5. **Visit**: http://localhost:8000/docs

### Using Docker

```bash
# Build
docker build -t rag-chatbot-api .

# Run
docker run -p 8000:8000 --env-file .env rag-chatbot-api
```

## Architecture

```
┌─────────────┐
│   Client    │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  FastAPI    │
│  Backend    │
└──────┬──────┘
       │
       ├─────────► PostgreSQL (metadata, analytics)
       │
       ├─────────► Qdrant (vector search)
       │
       └─────────► OpenAI (embeddings, chat)
```

## CORS Configuration

The API allows requests from:
- `http://localhost:3000` (local development)
- `https://*.github.io` (GitHub Pages)
- `https://*.vercel.app` (Vercel deployments)
- `https://*.hf.space` (Hugging Face Spaces)

To add your frontend domain, update `src/main.py`:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://your-frontend.com",  # Add your domain
    ],
    ...
)
```

## Troubleshooting

### Space won't start
- Check **Logs** in Space settings
- Verify all environment variables are set correctly
- Ensure Qdrant URL includes port `:6333`

### Database connection errors
- Verify `DATABASE_URL` format is correct
- Check database service is running
- Ensure SSL mode is configured properly

### OpenAI errors
- Verify API key is valid
- Check you have billing enabled and credits
- Review rate limits

### Vector search not working
- Ensure Qdrant collection exists
- Verify vector dimensions match (768 for text-embedding-3-small)
- Check if data has been indexed

## Performance Considerations

**Hugging Face Spaces Free Tier:**
- 2 vCPU cores
- 16GB RAM
- Cold start time: ~30-60 seconds
- Automatic sleep after inactivity

For better performance:
- Upgrade to paid Space tier
- Use persistent storage for caching
- Optimize vector dimensions

## License

MIT License - see LICENSE file for details

## Support

- **Documentation**: [API Docs](https://YOUR_SPACE_NAME.hf.space/docs)
- **Issues**: Report issues on [GitHub](https://github.com/YOUR_USERNAME/YOUR_REPO/issues)
- **Discussions**: [Hugging Face Discussions](https://huggingface.co/spaces/YOUR_USERNAME/YOUR_SPACE_NAME/discussions)

## Related Projects

- Frontend: [Link to your Docusaurus site]
- Dataset: [Link if you have a Hugging Face dataset]

---

Built with ❤️ using FastAPI, Qdrant, and OpenAI
