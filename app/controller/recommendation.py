import uuid
from typing import List

from sqlalchemy.orm import Session

from app.controller.job import JobController
from app.controller.user_profile import UserProfileController
from app.models.recommendation import RankedJob, RecommendationResponse
from app.ranker import rank_jobs


class RecommendationController:
    def __init__(self, db: Session):
        self._user_ctrl = UserProfileController(db)
        self._job_ctrl = JobController(db)

    def get_recommendations(self, user_id: uuid.UUID) -> RecommendationResponse:
        user = self._user_ctrl.get_by_id(user_id)
        jobs = self._job_ctrl.list_active()
        ranked: List[RankedJob] = rank_jobs(user, jobs)
        return RecommendationResponse(user_id=user_id, ranked_jobs=ranked)
