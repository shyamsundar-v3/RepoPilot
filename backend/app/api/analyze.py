import asyncio
from concurrent.futures import ThreadPoolExecutor

from fastapi import APIRouter, HTTPException

from app.github_client.client import clone_repo, validate_github_url
from app.models.schemas import AnalyzeRequest, AnalyzeResponse
from app.orchestration.job_manager import job_manager
from app.orchestration.workflow import run_workflow

router = APIRouter()
_executor = ThreadPoolExecutor(max_workers=2)


@router.post("/api/analyze", response_model=AnalyzeResponse, status_code=202)
async def analyze(request: AnalyzeRequest):
    try:
        validate_github_url(request.repo_url)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    try:
        repo_id, path = clone_repo(request.repo_url)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Clone failed: {e}")

    job = job_manager.create(repo_id)
    loop = asyncio.get_event_loop()
    loop.run_in_executor(_executor, run_workflow, job.job_id, repo_id)

    return AnalyzeResponse(repo_id=repo_id, job_id=job.job_id)
