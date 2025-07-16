from fastapi import APIRouter, HTTPException, Depends
from db.db_manager import DatabaseManager
from routers.auth import verify_token
from pydantic import BaseModel
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/attendance", tags=["Attendance"])

# --- Singleton DB Dependency ---
db_manager_instance = None

def get_db_manager():
    global db_manager_instance
    if db_manager_instance is None:
        db_manager_instance = DatabaseManager()
    return db_manager_instance

# --- Response Schema ---
class AttendanceResponse(BaseModel):
    id: Optional[int] = None
    employee_id: str
    timestamp: str
    confidence_score: Optional[float] = None
    camera_id: Optional[int] = None
    event_type: Optional[str] = None
    work_status: Optional[str] = None
    notes: Optional[str] = None

# --- Routes ---

@router.get("/", response_model=List[AttendanceResponse])
def get_latest_attendance(
    limit: int = 50,
    db: DatabaseManager = Depends(get_db_manager),
    _=Depends(verify_token)
):
    try:
        records = db.get_attendance_records(limit=limit)
        return [
            AttendanceResponse(
                id=r.id,
                employee_id=r.employee_id,
                timestamp=str(r.timestamp),
                confidence_score=r.confidence_score,
                camera_id=r.camera_id,
                event_type=r.event_type,
                work_status=r.work_status,
                notes=r.notes
            )
            for r in records
        ]
    except Exception as e:
        logger.exception("Error fetching attendance records")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{employee_id}", response_model=List[AttendanceResponse])
def get_attendance_by_employee(
    employee_id: str,
    db: DatabaseManager = Depends(get_db_manager),
    _=Depends(verify_token)
):
    try:
        records = db.get_attendance_records(employee_id=employee_id)
        return [
            AttendanceResponse(
                id=r.id,
                employee_id=r.employee_id,
                timestamp=str(r.timestamp),
                confidence_score=r.confidence_score,
                camera_id=r.camera_id,
                event_type=r.event_type,
                work_status=r.work_status,
                notes=r.notes
            )
            for r in records
        ]
    except Exception as e:
        logger.exception(f"Error fetching attendance for {employee_id}")
        raise HTTPException(status_code=500, detail="Internal server error")
