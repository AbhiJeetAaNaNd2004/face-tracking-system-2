from fastapi import Depends
from sqlalchemy.orm import Session
from app.config import settings
from db.db_config import get_db_session, close_db_session

from typing import Generator

def get_db() -> Generator[Session, None, None]:
    db = get_db_session(settings.DATABASE_URL)
    try:
        yield db
    finally:
        close_db_session(db)
