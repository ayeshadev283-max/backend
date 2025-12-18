"""
Simple mock API server for testing ChatKit frontend
Provides /v1/query and /v1/feedback endpoints with realistic responses
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
from typing import Optional, List
import time

app = FastAPI(title="ChatKit Mock API", version="1.0.0")

# Enable CORS for Docusaurus dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request/Response Models
class QueryRequest(BaseModel):
    book_id: str
    chapter_number: int
    question: str
    user_id: str

class Source(BaseModel):
    title: str
    url: str
    page_number: Optional[int] = None

class QueryResponse(BaseModel):
    response_id: str
    answer: str
    sources: List[Source]
    latency_ms: int

class FeedbackRequest(BaseModel):
    response_id: str
    rating: str  # 'helpful' or 'not_helpful'
    comment: Optional[str] = None
    user_id: str

class FeedbackResponse(BaseModel):
    success: bool
    message: str

# Mock responses database
MOCK_RESPONSES = {
    "physical ai": {
        "answer": """**Physical AI** refers to artificial intelligence systems that are embodied in physical robots, enabling them to interact with the real world through sensors and actuators.

Unlike traditional AI that operates purely in digital environments, Physical AI must:
- Process sensory input from the physical world (vision, touch, proprioception)
- Execute motor actions with precise timing and coordination
- Deal with uncertainty, noise, and unpredictable environments
- Operate under physical constraints (gravity, friction, inertia)

This represents a fundamental challenge known as **Moravec's Paradox**: tasks that are easy for humans (like walking or grasping objects) are incredibly difficult for AI, while tasks that are hard for humans (like complex calculations) are easy for AI.""",
        "sources": [
            {"title": "Chapter 1: Introduction to Physical AI", "url": "/docs/chapters/01-introduction", "page_number": 1},
            {"title": "Embodied Cognition", "url": "/docs/chapters/module-0-foundations/embodied-intelligence", "page_number": 12}
        ]
    },
    "default": {
        "answer": """I can help answer questions about Physical AI, humanoid robotics, and the topics covered in this book!

Some topics I can assist with:
- **Embodied intelligence** and cognition
- **ROS 2** (Robot Operating System)
- **Digital twins** and simulation
- **NVIDIA Isaac** platform
- **Vision-Language-Action (VLA)** models
- Locomotion and motor control
- Sensor fusion and perception

What would you like to learn about?""",
        "sources": [
            {"title": "Table of Contents", "url": "/docs/chapters/01-introduction", "page_number": None}
        ]
    }
}

@app.get("/")
async def root():
    return {
        "service": "ChatKit Mock API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": ["/v1/query", "/v1/feedback"]
    }

@app.post("/v1/query", response_model=QueryResponse)
async def query(request: QueryRequest):
    """Mock query endpoint - returns realistic AI responses"""
    start_time = time.time()

    # Simple keyword matching for demo
    question_lower = request.question.lower()

    response_data = MOCK_RESPONSES.get("default")
    if any(keyword in question_lower for keyword in ["physical ai", "embodied", "moravec"]):
        response_data = MOCK_RESPONSES.get("physical ai")

    latency_ms = int((time.time() - start_time) * 1000) + 100  # Add simulated latency

    return QueryResponse(
        response_id=f"mock-{int(time.time() * 1000)}",
        answer=response_data["answer"],
        sources=response_data["sources"],
        latency_ms=latency_ms
    )

@app.post("/v1/feedback", response_model=FeedbackResponse)
async def feedback(request: FeedbackRequest):
    """Mock feedback endpoint"""
    print(f"[FEEDBACK] response_id={request.response_id}, rating={request.rating}, user_id={request.user_id}")

    return FeedbackResponse(
        success=True,
        message=f"Feedback '{request.rating}' recorded for response {request.response_id}"
    )

if __name__ == "__main__":
    print("=" * 60)
    print("ChatKit Mock API Server")
    print("=" * 60)
    print("Starting on http://localhost:8000")
    print("API Docs: http://localhost:8000/docs")
    print("=" * 60)

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
