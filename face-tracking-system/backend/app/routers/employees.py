from fastapi import APIRouter, HTTPException, Depends
from db.db_manager import DatabaseManager
from routers.auth import verify_token
from pydantic import BaseModel
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/employees", tags=["Employees"])

# --- Role-based access control ---
def require_admin(token_data=Depends(verify_token)):
    if token_data.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin privileges required")

# --- Singleton DB Dependency ---
db_manager_instance = None

def get_db_manager():
    global db_manager_instance
    if db_manager_instance is None:
        db_manager_instance = DatabaseManager()
    return db_manager_instance

# --- Pydantic Schemas ---
class EmployeeResponse(BaseModel):
    employee_id: str
    name: str
    department: Optional[str] = None
    designation: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

class EmployeeCreateRequest(BaseModel):
    employee_id: str
    name: str
    department: Optional[str] = None
    designation: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None

class EmployeeUpdateRequest(BaseModel):
    name: Optional[str]
    department: Optional[str]
    designation: Optional[str]
    email: Optional[str]
    phone: Optional[str]

class DeleteResponse(BaseModel):
    deleted: bool
    message: str = ""

# --- CRUD Routes ---

@router.get("/", response_model=List[EmployeeResponse])
def list_employees(
    db: DatabaseManager = Depends(get_db_manager),
    _=Depends(verify_token)
):
    try:
        employees = db.get_all_employees()
        return [EmployeeResponse(
            employee_id=emp.id,
            name=emp.employee_name,
            department=emp.department,
            designation=emp.designation,
            email=emp.email,
            phone=emp.phone,
            created_at=str(emp.created_at),
            updated_at=str(emp.updated_at)
        ) for emp in employees]
    except Exception as e:
        logger.exception("Error listing employees")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{employee_id}", response_model=EmployeeResponse)
def get_employee(
    employee_id: str,
    db: DatabaseManager = Depends(get_db_manager),
    _=Depends(verify_token)
):
    try:
        emp = db.get_employee(employee_id)
        if not emp:
            raise HTTPException(status_code=404, detail="Employee not found")
        return EmployeeResponse(
            employee_id=emp.id,
            name=emp.employee_name,
            department=emp.department,
            designation=emp.designation,
            email=emp.email,
            phone=emp.phone,
            created_at=str(emp.created_at),
            updated_at=str(emp.updated_at)
        )
    except Exception as e:
        logger.exception("Error getting employee")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/", response_model=EmployeeResponse)
def create_employee(
    request: EmployeeCreateRequest,
    db: DatabaseManager = Depends(get_db_manager),
    _=Depends(require_admin)
):
    try:
        created = db.create_employee(
            employee_id=request.employee_id,
            employee_name=request.name,
            department=request.department,
            designation=request.designation,
            email=request.email,
            phone=request.phone
        )
        if not created:
            raise HTTPException(status_code=400, detail="Employee already exists")
        emp = db.get_employee(request.employee_id)
        return EmployeeResponse(
            employee_id=emp.id,
            name=emp.employee_name,
            department=emp.department,
            designation=emp.designation,
            email=emp.email,
            phone=emp.phone,
            created_at=str(emp.created_at),
            updated_at=str(emp.updated_at)
        )
    except Exception as e:
        logger.exception("Error creating employee")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("/{employee_id}", response_model=EmployeeResponse)
def update_employee(
    employee_id: str,
    request: EmployeeUpdateRequest,
    db: DatabaseManager = Depends(get_db_manager),
    _=Depends(require_admin)
):
    try:
        emp = db.get_employee(employee_id)
        if not emp:
            raise HTTPException(status_code=404, detail="Employee not found")

        # Update in DB (assumes you'll implement an update_employee method in DB)
        db.update_employee(
            employee_id=employee_id,
            name=request.name,
            department=request.department,
            designation=request.designation,
            email=request.email,
            phone=request.phone
        )

        emp = db.get_employee(employee_id)
        return EmployeeResponse(
            employee_id=emp.id,
            name=emp.employee_name,
            department=emp.department,
            designation=emp.designation,
            email=emp.email,
            phone=emp.phone,
            created_at=str(emp.created_at),
            updated_at=str(emp.updated_at)
        )
    except Exception as e:
        logger.exception("Error updating employee")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/{employee_id}", response_model=DeleteResponse)
def delete_employee(
    employee_id: str,
    db: DatabaseManager = Depends(get_db_manager),
    _=Depends(require_admin)
):
    try:
        success = db.delete_employee(employee_id)
        return DeleteResponse(
            deleted=success,
            message="Employee deleted" if success else "Employee not found"
        )
    except Exception as e:
        logger.exception("Error deleting employee")
        raise HTTPException(status_code=500, detail="Internal server error")