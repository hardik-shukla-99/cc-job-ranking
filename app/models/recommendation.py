import uuid
from typing import List

from pydantic import BaseModel

from app.models.job import JobResponse


class RankedJob(BaseModel):
    job: JobResponse
    score: float
    match_reasons: List[str]


class RecommendationResponse(BaseModel):
    user_id: uuid.UUID
    ranked_jobs: List[RankedJob]
