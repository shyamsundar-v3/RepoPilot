import json
import logging
import threading
import uuid
from dataclasses import dataclass, field
from typing import Any

from app.core.config import settings
from app.models.schemas import JobStatus, ReportResponse

logger = logging.getLogger(__name__)


@dataclass
class Job:
    job_id: str
    repo_id: str
    status: JobStatus = JobStatus.PENDING
    report: ReportResponse | None = None
    error: str | None = None


class JobManager:
    def __init__(self):
        self._jobs: dict[str, Job] = {}
        self._lock = threading.Lock()

    def create(self, repo_id: str) -> Job:
        job_id = uuid.uuid4().hex[:12]
        job = Job(job_id=job_id, repo_id=repo_id)
        with self._lock:
            self._jobs[job_id] = job
        return job

    def get(self, job_id: str) -> Job | None:
        return self._jobs.get(job_id)

    def set_running(self, job_id: str):
        job = self._jobs.get(job_id)
        if job:
            job.status = JobStatus.RUNNING

    def set_done(self, job_id: str, report: ReportResponse):
        job = self._jobs.get(job_id)
        if job:
            job.status = JobStatus.DONE
            job.report = report
        # Persist to disk so the report survives a server restart, not just
        # this in-memory dict.
        self._save_report_to_disk(job.repo_id if job else None, report)

    def set_error(self, job_id: str, error: str):
        job = self._jobs.get(job_id)
        if job:
            job.status = JobStatus.ERROR
            job.error = error

    def find_by_repo(self, repo_id: str) -> Job | None:
        """Find the latest completed or errored job for a repo.
        Prioritises DONE jobs; falls back to ERROR so the frontend
        can stop polling and display the error."""
        done_job = None
        error_job = None
        for job in self._jobs.values():
            if job.repo_id == repo_id:
                if job.status == JobStatus.DONE:
                    done_job = job
                elif job.status == JobStatus.ERROR:
                    error_job = job
        return done_job or error_job

    # ------------------------------------------------------------------
    # Disk persistence
    # ------------------------------------------------------------------

    def _report_path(self, repo_id: str):
        return settings.reports_dir / f"{repo_id}.json"

    def _save_report_to_disk(self, repo_id: str | None, report: ReportResponse):
        if not repo_id:
            return
        try:
            settings.reports_dir.mkdir(parents=True, exist_ok=True)
            path = self._report_path(repo_id)
            path.write_text(report.model_dump_json(indent=2), encoding="utf-8")
        except Exception:
            # Persistence is a nice-to-have; never let a disk error take
            # down an otherwise-successful analysis job.
            logger.exception("Failed to persist report for repo %s to disk", repo_id)

    def load_report_from_disk(self, repo_id: str) -> ReportResponse | None:
        path = self._report_path(repo_id)
        if not path.is_file():
            return None
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return ReportResponse(**data)
        except Exception:
            logger.exception("Failed to load persisted report for repo %s", repo_id)
            return None


job_manager = JobManager()
