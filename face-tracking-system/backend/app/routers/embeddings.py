from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.concurrency import run_in_threadpool
from core.face_enroller import FaceEnroller
from core.fts_system import FaceTrackingPipeline
from pydantic import BaseModel
import numpy as np
import cv2
import logging
import os
import jwt

# Setup logging
logger = logging.getLogger(__name__)

# Security setup
SECRET_KEY = os.getenv("SECRET_KEY", "insecure-default")
ALGORITHM = "HS256"
security = HTTPBearer()

# JWT Verification & Role Control
def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("status") != "active":
            raise HTTPException(status_code=403, detail="Account suspended or inactive")
        return payload
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")


def require_admin(token_data=Depends(verify_token)):
    if token_data.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin privileges required")
    return token_data


# Response schema
class EnrollmentResponse(BaseModel):
    success: bool
    message: str = ""


# Router setup
router = APIRouter(prefix="/embeddings", tags=["Embeddings"])


# Dependency Management: Singleton Pattern
class EnrollerSingleton:
    instance = None

    @classmethod
    def get_instance(cls):
        if cls.instance is None:
            pipeline = FaceTrackingPipeline()
            cls.instance = FaceEnroller(tracking_system=pipeline.system)
        return cls.instance


# Image processing helper
def process_image_from_upload(file_bytes: bytes) -> np.ndarray:
    np_array = np.frombuffer(file_bytes, np.uint8)
    return cv2.imdecode(np_array, cv2.IMREAD_COLOR)


# API Endpoints

@router.post("/enroll/", response_model=EnrollmentResponse)
async def enroll_employee(
    employee_id: str = Form(...),
    employee_name: str = Form(...),
    update_existing: bool = Form(False),
    files: list[UploadFile] = File(...),
    _=Depends(require_admin),
    enroller: FaceEnroller = Depends(EnrollerSingleton.get_instance)
):
    try:
        images = []
        for file in files:
            file_bytes = await file.read()
            image = await run_in_threadpool(process_image_from_upload, file_bytes)
            if image is not None:
                images.append(image)

        success = await run_in_threadpool(
            enroller.enroll_from_images,
            employee_id,
            employee_name,
            images,
            update_existing
        )
        return EnrollmentResponse(success=success, message="Enrollment completed")

    except Exception as e:
        logger.exception("Error during employee enrollment")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/add/", response_model=EnrollmentResponse)
async def add_embedding(
    employee_id: str = Form(...),
    file: UploadFile = File(...),
    _=Depends(require_admin),
    enroller: FaceEnroller = Depends(EnrollerSingleton.get_instance)
):
    try:
        file_bytes = await file.read()
        image = await run_in_threadpool(process_image_from_upload, file_bytes)

        if image is None:
            raise HTTPException(status_code=400, detail="Invalid image format")

        success = await run_in_threadpool(enroller.add_embedding, employee_id, image)
        return EnrollmentResponse(success=success, message="Embedding added")

    except Exception as e:
        logger.exception("Error adding embedding")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/delete_all/{employee_id}", response_model=EnrollmentResponse)
async def delete_all_embeddings(
    employee_id: str,
    _=Depends(require_admin),
    enroller: FaceEnroller = Depends(EnrollerSingleton.get_instance)
):
    try:
        success = await run_in_threadpool(enroller.remove_all_embeddings, employee_id)
        return EnrollmentResponse(success=success, message="All embeddings deleted")
    except Exception as e:
        logger.exception("Error deleting embeddings")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/archive_all/{employee_id}", response_model=EnrollmentResponse)
async def archive_all_embeddings(
    employee_id: str,
    _=Depends(require_admin),
    enroller: FaceEnroller = Depends(EnrollerSingleton.get_instance)
):
    try:
        success = await run_in_threadpool(enroller.archive_all_embeddings, employee_id)
        return EnrollmentResponse(success=success, message="All embeddings archived")
    except Exception as e:
        logger.exception("Error archiving embeddings")
        raise HTTPException(status_code=500, detail="Internal server error")
