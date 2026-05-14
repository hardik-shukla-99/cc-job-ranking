import uuid
from typing import List

from pydantic import BaseModel


class JobCreate(BaseModel):
    title: str
    company: str
    required_skills: List[str] = []
    experience_min: int = 0
    location: str = ""
    remote: bool = False
    salary: int = 0
    description: str = ""


class JobResponse(BaseModel):
    id: uuid.UUID
    title: str
    company: str
    required_skills: List[str]
    experience_min: int
    location: str
    remote: bool
    salary: int
    description: str
    is_active: bool

    model_config = {"from_attributes": True}
