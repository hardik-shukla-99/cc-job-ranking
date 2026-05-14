from typing import List

from sqlalchemy.orm import Session

from app.db.models.job import JobModel
from app.db.services.job import JobDB
from app.models.job import JobCreate


class JobController:
    def __init__(self, db: Session):
        self._db = JobDB(db)

    def create(self, payload: JobCreate) -> JobModel:
        return self._db.create(payload.model_dump())

    def list_active(self) -> List[JobModel]:
        return self._db.get_active_jobs()
