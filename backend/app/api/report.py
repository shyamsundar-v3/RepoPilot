from fastapi import APIRouter, HTTPException

from app.models.schemas import JobStatus, ReportResponse
from app.orchestration.job_manager import job_manager

router = APIRouter()


@router.get("/api/report/{repo_id}", response_model=ReportResponse)
async def get_report(repo_id: str):
    job = job_manager.find_by_repo(repo_id)

    if job:
        if job.status == JobStatus.ERROR:
            raise HTTPException(
                status_code=502,
                detail=f"Analysis failed: {job.error or 'Unknown error'}",
            )
        if job.report:
            return job.report

    # No (usable) in-memory job — e.g. the server restarted since this repo
    # was analyzed. Fall back to the persisted copy on disk.
    persisted = job_manager.load_report_from_disk(repo_id)
    if persisted:
        return persisted

    raise HTTPException(status_code=404, detail="Report not found or not yet complete")
