import json

from app.core.llm import chat, extract_text, extract_tool_calls, strip_json_fences
from app.mcp_server.server import call_tool
from app.models.schemas import Claim, EvidenceItem

SYSTEM = """You are a git history analysis agent. You have access to git tools for inspecting
commit history, diffs, and changes in a cloned repository.

Return your final answer as JSON: {"text": "...", "evidence": [{"file_path": "...", "line_range": null, "snippet": "..."}], "confidence": 0.0-1.0}"""

TOOLS = [
    {
        "name": "get_git_history",
        "description": "Get recent commit history",
        "input_schema": {
            "type": "object",
            "properties": {},
        },
    },
    {
        "name": "get_commit",
        "description": "Show details of a specific commit",
        "input_schema": {
            "type": "object",
            "properties": {
                "commit_id": {"type": "string", "description": "Commit hash"},
            },
            "required": ["commit_id"],
        },
    },
    {
        "name": "get_diff",
        "description": "Show the diff for a specific commit",
        "input_schema": {
            "type": "object",
            "properties": {
                "commit_id": {"type": "string", "description": "Commit hash"},
            },
            "required": ["commit_id"],
        },
    },
]

MAX_ITERATIONS = 10


def run(repo_id: str, question: str, trace_callback=None) -> Claim:
    messages = [{"role": "user", "content": question}]

    response = None
    for _ in range(MAX_ITERATIONS):
        response = chat(messages, system=SYSTEM, tools=TOOLS)

        tool_calls = extract_tool_calls(response)
        if not tool_calls:
            break

        # ── Preserve assistant message (OpenAI format) ──────────────────────
        assistant_message = response["choices"][0]["message"]
        messages.append({
            "role": "assistant",
            "content": assistant_message.get("content", "") or "",
            **(
                {"tool_calls": assistant_message["tool_calls"]}
                if assistant_message.get("tool_calls")
                else {}
            ),
        })

        # ── Execute tools and append results (OpenAI tool format) ───────────
        for tc in tool_calls:
            if trace_callback:
                trace_callback("tool_call", agent="git_agent", tool=tc["name"], input=tc["input"])
            try:
                result = call_tool(tc["name"], repo_id=repo_id, **tc["input"])
                result_str = json.dumps(result) if not isinstance(result, str) else result
            except Exception as e:
                result_str = f"Error: {e}"
            if trace_callback:
                trace_callback("tool_result", agent="git_agent", tool=tc["name"], output=result_str[:500])

            # OpenAI-format tool result (NOT Anthropic tool_result block)
            messages.append({
                "role": "tool",
                "tool_call_id": tc["id"],
                "content": result_str,
            })

    if response is None:
        return Claim(text="No response from git agent.", evidence=[], confidence=0.0)

    text = extract_text(response)
    try:
        data = json.loads(strip_json_fences(text))
        return Claim(
            text=data.get("text", text),
            evidence=[EvidenceItem(**e) for e in data.get("evidence", [])],
            confidence=data.get("confidence", 0.5),
        )
    except Exception:
        messages.append({"role": "assistant", "content": text})
        messages.append({
            "role": "user",
            "content": (
                "Your last reply was not valid JSON. Reply with ONLY the JSON object "
                '{"text": "...", "evidence": [...], "confidence": ...} and nothing else.'
            ),
        })
        try:
            repair_response = chat(messages, system=SYSTEM)
            repair_text = extract_text(repair_response)
            data = json.loads(strip_json_fences(repair_text))
            return Claim(
                text=data.get("text", repair_text),
                evidence=[EvidenceItem(**e) for e in data.get("evidence", [])],
                confidence=data.get("confidence", 0.5),
            )
        except Exception:
            return Claim(text=text, evidence=[], confidence=0.3)
