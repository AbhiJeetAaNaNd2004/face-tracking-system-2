from fastapi import APIRouter, HTTPException, Request, Depends
from fastapi.responses import StreamingResponse
from core.fts_system import FaceTrackingPipeline, generate_mjpeg
from utils.security import verify_token
from utils.logging import get_logger
from tasks.camera_tasks import stream_manager
from app.config import settings

logger = get_logger(__name__)


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
    """
    Stream video from a specific camera with face detection overlay.
    Includes stream management to prevent resource conflicts.
    """
    
    # Check if too many streams are active
    if stream_manager.get_total_streams() >= settings.MAX_CONCURRENT_STREAMS:
        raise HTTPException(
            status_code=503, 
            detail="Maximum number of concurrent streams reached"
        )
    
    # Check camera-specific stream limit
    if stream_manager.get_active_stream_count(camera_id) >= 3:
        raise HTTPException(
            status_code=503,
            detail=f"Too many active streams for camera {camera_id}"
        )
    
    pipeline = PipelineSingleton.get_pipeline()
    
    async def safe_stream():
        """Safe streaming generator with proper resource management."""
        try:
            with stream_manager.get_stream(camera_id) as cap:
                for frame in generate_mjpeg(camera_id, cap):
                    # Check if client disconnected
                    if await request.is_disconnected():
                        logger.info(f"Client disconnected from camera {camera_id}")
                        break
                    yield frame
                    
        except RuntimeError as e:
            logger.error(f"Stream resource error for camera {camera_id}: {e}")
            # Send error frame or handle gracefully
            return
        except Exception as e:
            logger.error(f"Stream error for camera {camera_id}: {e}")
            return

    logger.info(
        f"🔴 Stream started for camera {camera_id} by user {user.get('sub')} "
        f"(Active streams: {stream_manager.get_total_streams()})"
    )

    return StreamingResponse(
        safe_stream(),
        media_type="multipart/x-mixed-replace; boundary=frame",
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0"
        }
    )

@router.get("/status/{camera_id}")
async def get_camera_status(camera_id: int, user=Depends(verify_token)):
    """Get status information for a specific camera."""
    try:
        active_streams = stream_manager.get_active_stream_count(camera_id)
        
        # Test camera availability
        try:
            import cv2
            cap = cv2.VideoCapture(camera_id)
            is_available = cap.isOpened()
            cap.release()
        except Exception:
            is_available = False
        
        return {
            "camera_id": camera_id,
            "is_available": is_available,
            "active_streams": active_streams,
            "max_streams": 3
        }
        
    except Exception as e:
        logger.error(f"Error getting camera {camera_id} status: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/")
async def list_stream_status(user=Depends(verify_token)):
    """Get status of all streaming resources."""
    try:
        return {
            "total_active_streams": stream_manager.get_total_streams(),
            "max_concurrent_streams": settings.MAX_CONCURRENT_STREAMS,
            "available_slots": settings.MAX_CONCURRENT_STREAMS - stream_manager.get_total_streams()
        }
    except Exception as e:
        logger.error(f"Error getting stream status: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
