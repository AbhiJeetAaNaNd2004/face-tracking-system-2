from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from routers import streaming, embeddings, employees, attendance, auth
import logging
import os

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("FaceTrackingSystem")

# CORS origins: adjust for production!
ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    os.getenv("FRONTEND_URL", "https://your-production-frontend.com")
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 Starting Face Tracking System API")
    yield
    logger.info("🛑 Shutting down Face Tracking System API")


app = FastAPI(
    title="Face Tracking System API",
    description="Backend for face detection, recognition, and tracking.",
    version="1.0.0",
    lifespan=lifespan
)

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(streaming.router)
app.include_router(embeddings.router)
app.include_router(employees.router)
app.include_router(attendance.router)


@app.get("/")
async def root():
    return {"message": "Face Tracking System API Running"}
