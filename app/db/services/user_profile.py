from sqlalchemy.orm import Session

from app.db.models.user_profile import UserProfileModel
from app.db.services.base import BaseDB


class UserProfileDB(BaseDB[UserProfileModel]):
    def __init__(self, db: Session):
        super().__init__(db, UserProfileModel)
