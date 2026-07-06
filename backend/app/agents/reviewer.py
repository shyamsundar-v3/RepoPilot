import json
import re

from app.core.llm import chat, extract_text, strip_json_fences
from app.core.config import settings
from app.mcp_server.tools.filesystem import list_files, read_file
from app.models.schemas import Claim

SYSTEM = """You are a critical reviewer agent. You receive a claim with supporting evidence and must verify:
1. Every cited file_path actually exists in the repository.
2. Every cited snippet actually appears in that file.
3. The evidence logically supports the claim.

Return JSON: {"verdict": "sufficient" | "insufficient", "reason": "...", "confidence_adjustment": 0.0-1.0}

Be strict. If a file path does not exist or a snippet cannot be found, verdict must be "insufficient"."""


def _normalize_whitespace(text: str) -> str:
    """Collapse all runs of whitespace (spaces, tabs, newlines) to a single
    space. Models frequently re-wrap or re-indent a multi-line snippet
    slightly differently than the source file when embedding it in a JSON
    string — an exact-substring check would wrongly reject a correct
    citation over formatting alone, triggering a needless re-investigation."""
    return re.sub(r"\s+", " ", text).strip()


def run(repo_id: str, claim: Claim, trace_callback=None) -> dict:
    if trace_callback:
        trace_callback("reviewer", agent="reviewer", message=f"Reviewing claim: {claim.text[:100]}...")

    # Normalize all paths to forward slashes so Windows backslash paths
    # from list_files() don't cause false "FILE NOT FOUND" mismatches
    # when the LLM cites paths using forward slashes.
    all_files = {p.replace("\\", "/") for p in list_files(repo_id)}
    verification_notes = []

    for ev in claim.evidence:
        # Normalize the evidence path the same way
        norm_path = ev.file_path.replace("\\", "/")
        if norm_path not in all_files:
            verification_notes.append(f"FILE NOT FOUND: {ev.file_path}")
        elif ev.snippet:
            try:
                content = read_file(repo_id, ev.file_path)
                # Whitespace-tolerant containment check instead of a raw
                # substring match — see _normalize_whitespace above.
                if _normalize_whitespace(ev.snippet) not in _normalize_whitespace(content):
                    verification_notes.append(f"SNIPPET NOT FOUND in {ev.file_path}: {ev.snippet[:60]}...")
            except Exception as e:
                verification_notes.append(f"ERROR reading {ev.file_path}: {e}")

    evidence_summary = json.dumps([e.model_dump() for e in claim.evidence], indent=2)
    verification_context = "\n".join(verification_notes) if verification_notes else "All files and snippets verified."

    messages = [{
        "role": "user",
        "content": (
            f"CLAIM: {claim.text}\n\n"
            f"EVIDENCE:\n{evidence_summary}\n\n"
            f"VERIFICATION:\n{verification_context}\n\n"
            f"Original confidence: {claim.confidence}\n\n"
            "Give your verdict."
        ),
    }]

    response = chat(messages, system=SYSTEM, model=settings.llm_model_lite)
    text = extract_text(response)

    try:
        result = json.loads(strip_json_fences(text))
    except json.JSONDecodeError:
        # Give the reviewer one chance to fix its formatting before falling
        # back to a placeholder score. Previously any malformed JSON here
        # immediately became a flat 0.3 confidence regardless of how good
        # the underlying claim actually was — a meaningless number that
        # looked like a real (low) quality signal to the end user.
        repair_messages = messages + [
            {"role": "assistant", "content": text},
            {
                "role": "user",
                "content": (
                    "Your last reply was not valid JSON. Reply with ONLY the JSON object "
                    '{"verdict": "sufficient" | "insufficient", "reason": "...", '
                    '"confidence_adjustment": 0.0-1.0} and nothing else.'
                ),
            },
        ]
        try:
            repair_response = chat(repair_messages, system=SYSTEM, model=settings.llm_model_lite)
            repair_text = extract_text(repair_response)
            result = json.loads(strip_json_fences(repair_text))
        except json.JSONDecodeError:
            # Still couldn't get valid JSON — genuinely fall back, but say
            # so plainly rather than implying a real low-confidence verdict.
            result = {
                "verdict": "sufficient",
                "reason": "Reviewer returned unparseable output twice — confidence not independently verified.",
                "confidence_adjustment": 0.3,
            }

    if trace_callback:
        trace_callback("reviewer", agent="reviewer",
                        message=f"Verdict: {result.get('verdict')} — {result.get('reason', '')[:100]}")

    return result
