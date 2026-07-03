import json

from app.core.llm import chat, extract_text, strip_json_fences
from app.core.config import settings
from app.models.schemas import Claim, EvidenceItem
from app.rag.retriever import retrieve

SYSTEM = """You are a documentation analysis agent. You will receive relevant documentation chunks
from the repository. Answer questions based on this documentation.

Return your final answer as JSON: {"text": "...", "evidence": [{"file_path": "...", "line_range": null, "snippet": "..."}], "confidence": 0.0-1.0}"""


def run(repo_id: str, question: str, trace_callback=None) -> Claim:
    if trace_callback:
        trace_callback("tool_call", agent="docs_agent", tool="rag_retrieve", input={"query": question})

    chunks = retrieve(repo_id, question, top_k=5)

    if trace_callback:
        trace_callback("tool_result", agent="docs_agent", tool="rag_retrieve",
                        output=f"{len(chunks)} chunks retrieved")

    if not chunks:
        return Claim(text="No documentation found.", evidence=[], confidence=0.1)

    context = "\n\n---\n\n".join(
        f"[{c['file']}] chunk {c['chunk_index']}:\n{c['text']}" for c in chunks
    )

    messages = [{"role": "user", "content": f"Context:\n{context}\n\nQuestion: {question}"}]
    response = chat(messages, system=SYSTEM, model=settings.llm_model_lite)
    text = extract_text(response)

    try:
        data = json.loads(strip_json_fences(text))
        return Claim(
            text=data.get("text", text),
            evidence=[EvidenceItem(**e) for e in data.get("evidence", [])],
            confidence=data.get("confidence", 0.5),
        )
    except Exception:
        repair_messages = messages + [
            {"role": "assistant", "content": text},
            {
                "role": "user",
                "content": (
                    "Your last reply was not valid JSON. Reply with ONLY the JSON object "
                    '{"text": "...", "evidence": [...], "confidence": ...} and nothing else.'
                ),
            },
        ]
        try:
            repair_response = chat(repair_messages, system=SYSTEM, model=settings.llm_model_lite)
            repair_text = extract_text(repair_response)
            data = json.loads(strip_json_fences(repair_text))
            return Claim(
                text=data.get("text", repair_text),
                evidence=[EvidenceItem(**e) for e in data.get("evidence", [])],
                confidence=data.get("confidence", 0.5),
            )
        except Exception:
            return Claim(text=text, evidence=[], confidence=0.3)
