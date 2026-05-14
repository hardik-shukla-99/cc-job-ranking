import uuid
from typing import List

from pydantic import BaseModel, EmailStr


class UserProfileCreate(BaseModel):
    name: str
    email: EmailStr
    skills: List[str] = []
    experience_years: int = 0
    preferred_roles: List[str] = []
    location: str = ""
    remote_ok: bool = False
    salary_min: int = 0


class UserProfileResponse(BaseModel):
    id: uuid.UUID
    name: str
    email: str
    skills: List[str]
    experience_years: int
    preferred_roles: List[str]
    location: str
    remote_ok: bool
    salary_min: int

    model_config = {"from_attributes": True}
