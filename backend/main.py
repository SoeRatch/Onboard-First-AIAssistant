import os
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import uvicorn
from fastapi.responses import FileResponse

from backend.rag import RAGEngine
from backend.routers.chat import router as chat_router
from backend.routers.onboard import router as onboard_router
from dotenv import load_dotenv
load_dotenv()
COMPANY_NAME = os.getenv("COMPANY_NAME")
# Paths
BACKEND_DIR = Path(__file__).parent
PROJECT_ROOT = BACKEND_DIR.parent
DATA_DIR = PROJECT_ROOT / "data"
KNOWLEDGE_FILE = DATA_DIR / "knowledge.json"
CHROMA_DIR = PROJECT_ROOT / "chroma_db"
FRONTEND_DIR = PROJECT_ROOT / "frontend"

app = FastAPI()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize RAG engine on startup."""
    print("Initializing RAG engine...")
    rag_engine = RAGEngine(KNOWLEDGE_FILE, CHROMA_DIR)
    rag_engine.initialize()
    app.state.rag_engine = rag_engine

    print("RAG engine ready")
    yield
    print("Shutting down...")

app.router.lifespan_context = lifespan

# Create FastAPI app
app = FastAPI(
    title=f"Onboard-First AI Assistant",
    description=f"AI assistant for {COMPANY_NAME} with onboarding capabilities",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(chat_router, prefix="/api")
app.include_router(onboard_router, prefix="/api")

@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "onboard-first-assistant"
    }

# Serve static frontend files
app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

@app.get("/")
async def serve_frontend():
    """Serve the main frontend page."""
    return FileResponse(FRONTEND_DIR / "index.html")


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )

# Run with: uvicorn backend.main:app --reload