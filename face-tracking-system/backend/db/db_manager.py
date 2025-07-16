from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func
from db_config import SessionLocal
from db_models import Employee, FaceEmbedding, AttendanceRecord, Role, TrackingRecord, SystemLog, User
import numpy as np
import pickle
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import psycopg2
from io import BytesIO
import threading

class DatabaseManager:
    def __init__(self):
        self.session_lock = threading.RLock()
        self.logger = logging.getLogger(__name__)
        self.Session = SessionLocal  # ✅ Set session factory

    def create_employee(self, employee_id: str, employee_name: str, department: str = None, designation: str = None, email: str = None, phone: str = None) -> bool:
        session = None
        try:
            session = self.Session()
            existing_employee = session.query(Employee).filter(Employee.id == employee_id).first()
            if existing_employee:
                return False
            employee = Employee(
                id=employee_id,
                employee_name=employee_name,
                department=department,
                designation=designation,
                email=email,
                phone=phone)
            session.add(employee)
            session.commit()
            return True
        except Exception as e:
            if session:
                session.rollback()
            self.logger.error(f"Error creating employee {employee_id}: {e}")
            return False
        finally:
            if session:
                session.close()

    def get_employee(self, employee_id: str) -> Optional[Employee]:
        session = None
        try:
            session = self.Session()
            return session.query(Employee).filter(Employee.id == employee_id).first()
        except Exception as e:
            self.logger.error(f"Error getting employee {employee_id}: {e}")
            return None
        finally:
            if session:
                session.close()

    def get_all_employees(self) -> List[Employee]:
        session = None
        try:
            session = self.Session()
            return session.query(Employee).filter(Employee.is_active == True).all()
        except Exception as e:
            self.logger.error(f"Error getting all employees: {e}")
            return []
        finally:
            if session:
                session.close()

    def store_face_embedding(self, employee_id, embedding, embedding_type, quality_score, source_image_path):
        session = None
        try:
            session = self.Session()

            # Serialize embedding to bytes
            out = BytesIO()
            np.save(out, embedding.astype(np.float32))
            out.seek(0)
            binary_embedding = out.read()

            new_embedding = FaceEmbedding(
                employee_id=employee_id,
                embedding_data=binary_embedding,
                embedding_type=embedding_type,
                quality_score=float(quality_score),
                source_image_path=source_image_path,
                is_active=True
            )
            session.add(new_embedding)
            session.commit()
            print(f"[DB] Stored embedding for {employee_id}")
            return True

        except Exception as e:
            if session:
                session.rollback()
            print(f"[DB] Error storing embedding for {employee_id}: {e}")
            return False

        finally:
            if session:
                session.close()

    def get_face_embeddings(self, employee_id: str = None, embedding_type: str = None, limit: int = None) -> List[Tuple[str, np.ndarray]]:
        session = None
        try:
            session = self.Session()
            query = session.query(FaceEmbedding).filter(FaceEmbedding.is_active == True)
            if employee_id:
                query = query.filter(FaceEmbedding.employee_id == employee_id)
            if embedding_type:
                query = query.filter(FaceEmbedding.embedding_type == embedding_type)
            query = query.order_by(desc(FaceEmbedding.created_at))
            if limit:
                query = query.limit(limit)
            results = []
            for embedding_record in query.all():
                # ✅ Deserialize bytes to numpy array
                embedding_data = np.load(BytesIO(embedding_record.embedding_data))
                results.append((embedding_record.employee_id, embedding_data))
            return results
        except Exception as e:
            self.logger.error(f"Error getting face embeddings: {e}")
            return []
        finally:
            if session:
                session.close()


    def get_all_active_embeddings(self) -> Tuple[List[np.ndarray], List[str]]:
        session = None
        try:
            session = self.Session()
            embeddings = []
            labels = []

            enroll_embeddings = session.query(FaceEmbedding).filter(
                and_(FaceEmbedding.is_active == True, FaceEmbedding.embedding_type == 'enroll')
            ).all()

            for emb_record in enroll_embeddings:
                embedding_data = pickle.loads(emb_record.embedding_data)
                embeddings.append(embedding_data)
                labels.append(emb_record.employee_id)

            update_embeddings = session.query(FaceEmbedding).filter(
                and_(FaceEmbedding.is_active == True, FaceEmbedding.embedding_type == 'update')
            ).order_by(desc(FaceEmbedding.created_at)).all()

            employee_update_count = {}
            for emb_record in update_embeddings:
                emp_id = emb_record.employee_id
                if emp_id not in employee_update_count:
                    employee_update_count[emp_id] = 0
                if employee_update_count[emp_id] < 3:
                    embedding_data = pickle.loads(emb_record.embedding_data)
                    embeddings.append(embedding_data)
                    labels.append(emb_record.employee_id)
                    employee_update_count[emp_id] += 1

            return embeddings, labels
        except Exception as e:
            self.logger.error(f"Error getting all active embeddings: {e}")
            return [], []
        finally:
            if session:
                session.close()

    def log_attendance(self, employee_id: str, camera_id: int, event_type: str, confidence_score: float = 0.0, work_status: str = 'working', notes: str = None) -> bool:
        session = None
        try:
            session = self.Session()
            attendance_record = AttendanceRecord(
                employee_id=employee_id,
                camera_id=camera_id,
                event_type=event_type,
                confidence_score=confidence_score,
                work_status=work_status,
                notes=notes)
            session.add(attendance_record)
            session.commit()
            return True
        except Exception as e:
            if session:
                session.rollback()
            self.logger.error(f"Error logging attendance for {employee_id}: {e}")
            return False
        finally:
            if session:
                session.close()

    def get_attendance_records(self, employee_id: str = None, start_date: datetime = None, end_date: datetime = None, limit: int = 100) -> List[AttendanceRecord]:
        session = None
        try:
            session = self.Session()
            query = session.query(AttendanceRecord).filter(AttendanceRecord.is_valid == True)
            if employee_id:
                query = query.filter(AttendanceRecord.employee_id == employee_id)
            if start_date:
                query = query.filter(AttendanceRecord.timestamp >= start_date)
            if end_date:
                query = query.filter(AttendanceRecord.timestamp <= end_date)
            query = query.order_by(desc(AttendanceRecord.timestamp))
            if limit:
                query = query.limit(limit)
            return query.all()
        except Exception as e:
            self.logger.error(f"Error getting attendance records: {e}")
            return []
        finally:
            if session:
                session.close()

    def get_latest_attendance_by_employee(self, employee_id: str, hours_back: int = 10) -> Optional[AttendanceRecord]:
        session = None
        try:
            session = self.Session()
            time_threshold = datetime.now() - timedelta(hours=hours_back)
            return session.query(AttendanceRecord).filter(
                and_(
                    AttendanceRecord.employee_id == employee_id,
                    AttendanceRecord.timestamp >= time_threshold,
                    AttendanceRecord.is_valid == True)
            ).order_by(desc(AttendanceRecord.timestamp)).first()
        except Exception as e:
            self.logger.error(f"Error getting latest attendance for {employee_id}: {e}")
            return None
        finally:
            if session:
                session.close()
    
    # 🔧 Implement similar pattern for other methods like store_tracking_record, cleanup_old_embeddings, log_system_event, create_role, get_role, create_user, get_user following the same session management.
    def delete_employee(self, employee_id: str) -> bool:
        session = None
        try:
            session = self.Session()
            employee = session.query(Employee).filter(Employee.id == employee_id).first()
            if not employee:
                return False
            session.query(FaceEmbedding).filter(FaceEmbedding.employee_id == employee_id).delete()
            session.query(AttendanceRecord).filter(AttendanceRecord.employee_id == employee_id).delete()
            session.delete(employee)
            session.commit()
            return True
        except Exception as e:
            if session:
                session.rollback()
            return False
        finally:
            if session:
                session.close()

    def delete_embeddings(self, employee_id: str) -> bool:
        session = None
        try:
            session = self.Session()
            session.query(FaceEmbedding).filter(FaceEmbedding.employee_id == employee_id).delete()
            session.commit()
            return True
        except Exception as e:
            if session:
                session.rollback()
            return False
        finally:
            if session:
                session.close()

    def remove_embedding(self, embedding_id: int) -> bool:
        session = None
        try:
            session = self.Session()
            embedding = session.query(FaceEmbedding).filter(FaceEmbedding.id == embedding_id).first()
            if not embedding:
                return False
            session.delete(embedding)
            session.commit()
            return True
        except Exception as e:
            if session:
                session.rollback()
            return False
        finally:
            if session:
                session.close()

    def archive_embeddings(self, employee_id: str) -> bool:
        session = None
        try:
            session = self.Session()
            session.query(FaceEmbedding).filter(FaceEmbedding.employee_id == employee_id).update({
                FaceEmbedding.is_active: False
            })
            session.commit()
            return True
        except Exception as e:
            if session:
                session.rollback()
            return False
        finally:
            if session:
                session.close()
    def get_user_by_username(self, username: str) -> Optional[User]:
        session = None
        try:
            session = self.Session()
            return session.query(User).filter(User.username == username).first()
        except Exception as e:
            self.logger.error(f"Error fetching user {username}: {e}")
            return None
        finally:
            if session:
                session.close()
    def update_user_status(self, user_id: int, new_status: str) -> bool:
        session = self.Session()
        try:
            user = session.query(User).filter(User.id == user_id).first()
            if not user:
                return False
            user.status = new_status
            session.commit()
            return True
        except:
            session.rollback()
            return False
        finally:
            session.close()