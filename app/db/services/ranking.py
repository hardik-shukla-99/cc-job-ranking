from typing import List

from app.db.models.job import JobModel
from app.db.models.user_profile import UserProfileModel
from app.models.job import JobResponse
from app.models.recommendation import RankedJob

_WEIGHTS = {
    "skills": 0.45,
    "role": 0.20,
    "experience": 0.15,
    "location": 0.10,
    "salary": 0.10,
}


def _skills_score(user_skills: List[str], job_skills: List[str]) -> tuple[float, str]:
    if not job_skills:
        return 1.0, "No specific skills required"
    u = {s.lower() for s in user_skills}
    j = {s.lower() for s in job_skills}
    matched = u & j
    ratio = len(matched) / len(j)
    reason = f"Skills matched: {', '.join(sorted(matched)) or 'none'} ({len(matched)}/{len(j)})"
    return ratio, reason


def _role_score(preferred_roles: List[str], job_title: str) -> tuple[float, str]:
    title_lower = job_title.lower()
    for role in preferred_roles:
        if role.lower() in title_lower:
            return 1.0, f"Role '{role}' matches job title"
    return 0.0, "Role preference not matched"


def _experience_score(user_years: int, exp_min: int) -> tuple[float, str]:
    if user_years < exp_min:
        return 0.0, f"Under-experienced (need {exp_min}y, have {user_years}y)"
    gap = user_years - exp_min
    score = max(0.5, 1.0 - (gap - 5) * 0.05) if gap > 5 else 1.0
    return score, f"Experience fit ({user_years}y, min {exp_min}y)"


def _location_score(user_loc: str, remote_ok: bool, job_loc: str, job_remote: bool) -> tuple[float, str]:
    if job_remote and remote_ok:
        return 1.0, "Remote position matches preference"
    if user_loc.lower() == job_loc.lower() and user_loc:
        return 1.0, f"Location match: {user_loc}"
    return 0.0, "Location mismatch"


def _salary_score(salary_min: int, job_salary: int) -> tuple[float, str]:
    if job_salary >= salary_min:
        return 1.0, f"Salary ${job_salary:,} meets minimum ${salary_min:,}"
    return 0.0, f"Salary ${job_salary:,} below minimum ${salary_min:,}"


class RankingService:
    def rank_jobs(self, user: UserProfileModel, jobs: List[JobModel]) -> List[RankedJob]:
        results: List[RankedJob] = []

        for job in jobs:
            s_score, s_reason = _skills_score(user.skills, job.required_skills)
            r_score, r_reason = _role_score(user.preferred_roles, job.title)
            e_score, e_reason = _experience_score(user.experience_years, job.experience_min)
            l_score, l_reason = _location_score(user.location, user.remote_ok, job.location, job.remote)
            p_score, p_reason = _salary_score(user.salary_min, job.salary)

            total = (
                s_score * _WEIGHTS["skills"]
                + r_score * _WEIGHTS["role"]
                + e_score * _WEIGHTS["experience"]
                + l_score * _WEIGHTS["location"]
                + p_score * _WEIGHTS["salary"]
            )

            results.append(
                RankedJob(
                    job=JobResponse.model_validate(job),
                    score=round(total, 4),
                    match_reasons=[s_reason, r_reason, e_reason, l_reason, p_reason],
                )
            )

        results.sort(key=lambda x: x.score, reverse=True)
        return results