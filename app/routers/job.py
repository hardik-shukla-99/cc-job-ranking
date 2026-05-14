from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.controller.job import JobController
from app.db.client import DBClient
from app.models.base import BaseResponse
from app.models.job import JobCreate, JobResponse

job_router = APIRouter(prefix="/jobs", tags=["Jobs"])


@job_router.post("", response_model=BaseResponse[JobResponse], status_code=201)
def create_job(
    payload: JobCreate,
    db: Session = Depends(DBClient.get_db_session),
) -> BaseResponse[JobResponse]:
    job = JobController(db).create(payload)
    return BaseResponse(
        status=201,
        message="Job created",
        payload=JobResponse.model_validate(job),
    )


@job_router.get("", response_model=BaseResponse[List[JobResponse]])
def list_jobs(
    db: Session = Depends(DBClient.get_db_session),
) -> BaseResponse[List[JobResponse]]:
    jobs = JobController(db).list_active()
    return BaseResponse(
        status=200,
        message="Active jobs retrieved",
        payload=[JobResponse.model_validate(j) for j in jobs],
    )
