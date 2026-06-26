from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field


class AnalyzeRequest(BaseModel):
    repo_url: str


class ChatRequest(BaseModel):
    repo_id: str
    question: str


class EvidenceItem(BaseModel):
    file_path: str
    line_range: str | None = None
    snippet: str | None = None


class Claim(BaseModel):
    text: str
    evidence: list[EvidenceItem] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)


class ReportSection(BaseModel):
    claims: list[Claim] = Field(default_factory=list)


class ReportResponse(BaseModel):
    repo_id: str
    overview: ReportSection
    architecture: ReportSection
    code_flow: ReportSection
    dependencies: ReportSection
    docs: ReportSection
    git_history: ReportSection
    dev_guide: ReportSection
    concerns: ReportSection


class TraceEventType(str, Enum):
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"
    REVIEWER = "reviewer"
    DONE = "done"
    ERROR = "error"


class TraceEvent(BaseModel):
    type: TraceEventType
    agent: str | None = None
    tool: str | None = None
    input: dict | None = None
    output: str | None = None
    message: str | None = None
    timestamp: float | None = None


class AnalyzeResponse(BaseModel):
    repo_id: str
    job_id: str


class ChatResponse(BaseModel):
    answer: str
    evidence: list[EvidenceItem] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)


class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    DONE = "done"
    ERROR = "error"
