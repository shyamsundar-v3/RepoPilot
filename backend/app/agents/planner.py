import json

from app.core.llm import chat, extract_text, strip_json_fences
from app.core.config import settings
from app.models.schemas import ReportResponse

SYSTEM = """You are a planning agent. Given a repository analysis task, decide which specialist agents
to invoke and in what order. Available agents: code_agent, docs_agent, git_agent.

For a full repository report, you must cover all sections:
overview, architecture, code_flow, dependencies, docs, git_history, dev_guide, concerns.

Return JSON: {"plan": [{"agent": "...", "question": "...", "section": "..."}]}

Each plan step maps to one report section. You may assign multiple steps to the same agent
with different questions."""

SECTION_AGENTS = {
    "overview": "code_agent",
    "architecture": "code_agent",
    "code_flow": "code_agent",
    "dependencies": "code_agent",
    "docs": "docs_agent",
    "git_history": "git_agent",
    "dev_guide": "docs_agent",
    "concerns": "code_agent",
}

SECTION_QUESTIONS = {
    "overview": "Provide a high-level overview of this project: what it does, what language/framework it uses, and its main entry points.",
    "architecture": "Describe the architecture of this project: directory structure, main modules, how they relate, and key design patterns used.",
    "code_flow": "Trace the main code flow: how a typical request or operation flows through the codebase from entry point to output.",
    "dependencies": "List and describe the project's key dependencies and what each is used for.",
    "docs": "Summarize the project's documentation: what the README says, any additional docs, and how well-documented the code is.",
    "git_history": "Analyze the git history: recent activity, main contributors, and notable changes.",
    "dev_guide": "Create a developer guide: how to set up the project, run it, run tests, and contribute.",
    "concerns": "Identify potential concerns: code smells, security issues, missing tests, outdated dependencies, or architectural problems.",
}


def create_full_report_plan() -> list[dict]:
    return [
        {"agent": SECTION_AGENTS[sec], "question": SECTION_QUESTIONS[sec], "section": sec}
        for sec in SECTION_AGENTS
    ]


def create_question_plan(question: str) -> list[dict]:
    messages = [{"role": "user", "content": f"Question about a repository: {question}"}]
    response = chat(messages, system=SYSTEM, model=settings.llm_model_lite)
    text = extract_text(response)
    try:
        data = json.loads(strip_json_fences(text))
        return data.get("plan", [{"agent": "code_agent", "question": question, "section": "overview"}])
    except json.JSONDecodeError:
        return [{"agent": "code_agent", "question": question, "section": "overview"}]
