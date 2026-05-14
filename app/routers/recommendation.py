import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.controller.recommendation import RecommendationController
from app.db.client import DBClient
from app.models.base import BaseResponse
from app.models.recommendation import RecommendationResponse

recommendation_router = APIRouter(prefix="/recommendations", tags=["Recommendations"])


@recommendation_router.get(
    "/{user_id}",
    response_model=BaseResponse[RecommendationResponse],
)
def get_recommendations(
    user_id: uuid.UUID,
    db: Session = Depends(DBClient.get_db_session),
) -> BaseResponse[RecommendationResponse]:
    result = RecommendationController(db).get_recommendations(user_id)
    return BaseResponse(
        status=200,
        message="Recommendations retrieved",
        payload=result,
    )
