import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed

from app.agents.planner import create_full_report_plan
from app.agents.code_agent import run as run_code_agent
from app.agents.docs_agent import run as run_docs_agent
from app.agents.git_agent import run as run_git_agent
from app.agents.reviewer import run as run_reviewer
from app.models.schemas import Claim, ReportResponse, ReportSection
from app.orchestration.trace_bus import trace_bus
from app.orchestration.job_manager import job_manager
from app.rag.ingest import ingest_repo

AGENT_RUNNERS = {
    "code_agent": run_code_agent,
    "docs_agent": run_docs_agent,
    "git_agent": run_git_agent,
}

MAX_RETRIES = 2
MAX_SECTION_WORKERS = 8  # one per report section — they're independent of each other


def _trace_callback_factory(job_id: str):
    def cb(event_type: str, **kwargs):
        trace_bus.emit_simple(job_id, event_type, **kwargs)
    return cb


def _run_section(job_id: str, repo_id: str, step: dict, trace_cb) -> tuple[str, ReportSection]:
    """Run one plan step (investigate + review + retries) end to end.
    Safe to call from multiple threads concurrently — each section has its
    own independent conversation/state, nothing here is shared/mutated
    across sections."""
    agent_name = step["agent"]
    question = step["question"]
    section = step["section"]

    trace_bus.emit_simple(job_id, "tool_call", agent=agent_name,
                           message=f"Investigating: {section}")

    runner = AGENT_RUNNERS.get(agent_name)
    if not runner:
        return section, ReportSection(claims=[
            Claim(text=f"No agent available: {agent_name}", evidence=[], confidence=0.0)
        ])

    claim = runner(repo_id, question, trace_callback=trace_cb)

    review = run_reviewer(repo_id, claim, trace_callback=trace_cb)
    verdict = review.get("verdict", "insufficient")
    adjusted_confidence = review.get("confidence_adjustment", claim.confidence)

    retries = 0
    while verdict == "insufficient" and retries < MAX_RETRIES:
        retries += 1
        trace_bus.emit_simple(job_id, "reviewer", agent="reviewer",
                               message=f"Re-investigating {section} (retry {retries})")
        claim = runner(
            repo_id,
            question + f"\n\nPrevious attempt was insufficient: {review.get('reason', '')}",
            trace_callback=trace_cb,
        )
        review = run_reviewer(repo_id, claim, trace_callback=trace_cb)
        verdict = review.get("verdict", "insufficient")
        adjusted_confidence = review.get("confidence_adjustment", claim.confidence)

    claim.confidence = adjusted_confidence
    return section, ReportSection(claims=[claim])


def run_workflow(job_id: str, repo_id: str):
    try:
        job_manager.set_running(job_id)
        trace_bus.emit_simple(job_id, "tool_call", agent="system", message="Starting analysis workflow")

        trace_bus.emit_simple(job_id, "tool_call", agent="system", tool="ingest", message="Ingesting docs for RAG")
        chunk_count = ingest_repo(repo_id)
        trace_bus.emit_simple(job_id, "tool_result", agent="system", tool="ingest",
                               output=f"Ingested {chunk_count} chunks")

        plan = create_full_report_plan()
        trace_bus.emit_simple(job_id, "tool_result", agent="planner",
                               output=f"Plan: {len(plan)} steps")

        trace_cb = _trace_callback_factory(job_id)
        sections: dict[str, ReportSection] = {}

        # Sections are independent (each is its own agent conversation), so
        # run them concurrently instead of one after another. This is the
        # single biggest lever on total wall-clock time for a full report.
        with ThreadPoolExecutor(max_workers=min(MAX_SECTION_WORKERS, len(plan))) as pool:
            futures = [
                pool.submit(_run_section, job_id, repo_id, step, trace_cb)
                for step in plan
            ]
            for future in as_completed(futures):
                section, result = future.result()
                sections[section] = result

        report = ReportResponse(
            repo_id=repo_id,
            overview=sections.get("overview", ReportSection()),
            architecture=sections.get("architecture", ReportSection()),
            code_flow=sections.get("code_flow", ReportSection()),
            dependencies=sections.get("dependencies", ReportSection()),
            docs=sections.get("docs", ReportSection()),
            git_history=sections.get("git_history", ReportSection()),
            dev_guide=sections.get("dev_guide", ReportSection()),
            concerns=sections.get("concerns", ReportSection()),
        )

        job_manager.set_done(job_id, report)
        trace_bus.emit_simple(job_id, "done", agent="system", message="Analysis complete")

    except Exception as e:
        job_manager.set_error(job_id, str(e))
        trace_bus.emit_simple(job_id, "error", agent="system", message=f"Workflow error: {e}")
        traceback.print_exc()
