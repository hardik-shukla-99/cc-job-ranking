import uuid

from sqlalchemy import Boolean, Integer, String, Text, text
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.client import Base


class UserProfileModel(Base):
    __tablename__ = "user_profiles"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    skills: Mapped[list[str]] = mapped_column(ARRAY(Text), nullable=False, default=list)
    experience_years: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    preferred_roles: Mapped[list[str]] = mapped_column(ARRAY(Text), nullable=False, default=list)
    location: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    remote_ok: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    salary_min: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
