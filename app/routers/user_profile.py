import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.controller.user_profile import UserProfileController
from app.db.client import DBClient
from app.models.base import BaseResponse
from app.models.user_profile import UserProfileCreate, UserProfileResponse

user_router = APIRouter(prefix="/users", tags=["Users"])


@user_router.post("", response_model=BaseResponse[UserProfileResponse], status_code=201)
def create_user(
    payload: UserProfileCreate,
    db: Session = Depends(DBClient.get_db_session),
) -> BaseResponse[UserProfileResponse]:
    user = UserProfileController(db).create(payload)
    return BaseResponse(
        status=201,
        message="User profile created",
        payload=UserProfileResponse.model_validate(user),
    )


@user_router.get("/{user_id}", response_model=BaseResponse[UserProfileResponse])
def get_user(
    user_id: uuid.UUID,
    db: Session = Depends(DBClient.get_db_session),
) -> BaseResponse[UserProfileResponse]:
    user = UserProfileController(db).get_by_id(user_id)
    return BaseResponse(
        status=200,
        message="User profile retrieved",
        payload=UserProfileResponse.model_validate(user),
    )
