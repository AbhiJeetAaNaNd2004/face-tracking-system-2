from fastapi import APIRouter, HTTPException, Request, Depends
from fastapi.responses import StreamingResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from core.fts_system import FaceTrackingPipeline, generate_mjpeg
import logging
import jwt
import os

logger = logging.getLogger(__name__)

# Setup Security
SECRET_KEY = os.getenv("SECRET_KEY", "change-this-secret")
ALGORITHM = "HS256"
security = HTTPBearer()


def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("status") != "active":
            raise HTTPException(status_code=403, detail="Account inactive or suspended")
        return payload
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid authentication token")


# Router Setup
router = APIRouter(prefix="/stream", tags=["Streaming"])

# Singleton Pipeline Manager
class PipelineSingleton:
    instance = None

    @classmethod
    def get_pipeline(cls):
        if cls.instance is None:
            cls.instance = FaceTrackingPipeline()
        return cls.instance


@router.get("/{camera_id}")
async def stream_camera(camera_id: int, request: Request, user=Depends(verify_token)):
    pipeline = PipelineSingleton.get_pipeline()

    async def safe_stream():
        try:
            for frame in generate_mjpeg(camera_id):
                if await request.is_disconnected():
                    logger.info(f"Client disconnected from camera {camera_id}")
                    break
                yield frame
        except Exception as e:
            logger.exception(f"Stream error for camera {camera_id}")
            return

    logger.info(f"🔴 Stream started for camera {camera_id} by user {user.get('sub')}")

    return StreamingResponse(
        safe_stream(),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )
