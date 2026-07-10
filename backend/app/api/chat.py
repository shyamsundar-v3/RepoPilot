import asyncio
from concurrent.futures import ThreadPoolExecutor

from fastapi import APIRouter, HTTPException

from app.agents.planner import create_question_plan
from app.agents.code_agent import run as run_code_agent
from app.agents.docs_agent import run as run_docs_agent
from app.agents.git_agent import run as run_git_agent
from app.agents.reviewer import run as run_reviewer
from app.github_client.client import get_repo_path
from app.models.schemas import ChatRequest, ChatResponse

router = APIRouter()
_executor = ThreadPoolExecutor(max_workers=4)

AGENT_RUNNERS = {
    "code_agent": run_code_agent,
    "docs_agent": run_docs_agent,
    "git_agent": run_git_agent,
}


def _run_chat_plan(repo_id: str, question: str):
    plan = create_question_plan(question)
    claims = []
    for step in plan:
        agent_name = step.get("agent", "code_agent")
        step_question = step.get("question", question)
        runner = AGENT_RUNNERS.get(agent_name, run_code_agent)
        claim = runner(repo_id, step_question)
        review = run_reviewer(repo_id, claim)
        claim.confidence = review.get("confidence_adjustment", claim.confidence)
        claims.append(claim)
    return claims


@router.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    try:
        get_repo_path(request.repo_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Repo {request.repo_id} not found. Analyze it first.")

    loop = asyncio.get_event_loop()
    claims = await loop.run_in_executor(_executor, _run_chat_plan, request.repo_id, request.question)

    if not claims:
        return ChatResponse(answer="No answer could be generated.", evidence=[], confidence=0.0)

    best = max(claims, key=lambda c: c.confidence)
    all_evidence = []
    for c in claims:
        all_evidence.extend(c.evidence)

    combined_text = "\n\n".join(c.text for c in claims) if len(claims) > 1 else best.text

    return ChatResponse(
        answer=combined_text,
        evidence=all_evidence,
        confidence=best.confidence,
    )
