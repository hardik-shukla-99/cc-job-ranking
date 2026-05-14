import uuid
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.db.models.user_profile import UserProfileModel
from app.db.services.user_profile import UserProfileDB
from app.models.user_profile import UserProfileCreate


class UserProfileController:
    def __init__(self, db: Session):
        self._db = UserProfileDB(db)

    def create(self, payload: UserProfileCreate) -> UserProfileModel:
        existing = self._db.get_by_filter(email=payload.email)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"User with email '{payload.email}' already exists",
            )
        return self._db.create(payload.model_dump())

    def get_by_id(self, user_id: uuid.UUID) -> UserProfileModel:
        user = self._db.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User {user_id} not found",
            )
        return user
