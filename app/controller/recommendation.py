import uuid
from typing import List

from sqlalchemy.orm import Session

from app.controller.job import JobController
from app.controller.user_profile import UserProfileController
from app.db.services.ranking import RankingService
from app.models.recommendation import RankedJob, RecommendationResponse


class RecommendationController:
    def __init__(self, db: Session):
        self._user_ctrl = UserProfileController(db)
        self._job_ctrl = JobController(db)
        self._ranking = RankingService()

    def get_recommendations(self, user_id: uuid.UUID) -> RecommendationResponse:
        user = self._user_ctrl.get_by_id(user_id)
        jobs = self._job_ctrl.list_active()
        ranked: List[RankedJob] = self._ranking.rank_jobs(user, jobs)
        return RecommendationResponse(user_id=user_id, ranked_jobs=ranked)
