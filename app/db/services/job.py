from typing import List

from sqlalchemy.orm import Session

from app.db.models.job import JobModel
from app.db.services.base import BaseDB


class JobDB(BaseDB[JobModel]):
    def __init__(self, db: Session):
        super().__init__(db, JobModel)

    def get_active_jobs(self) -> List[JobModel]:
        return self.db.query(JobModel).filter(JobModel.is_active.is_(True)).all()
