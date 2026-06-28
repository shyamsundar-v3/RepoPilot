import json

from app.core.llm import chat, extract_text, extract_tool_calls, strip_json_fences
from app.mcp_server.server import call_tool
from app.models.schemas import Claim, EvidenceItem


SYSTEM = """You are a code analysis agent. You have access to tools for reading and searching
a cloned repository. Answer questions about the code with specific file paths and line references.

Return your final answer as JSON:
{
  "text": "...",
  "evidence": [
    {
      "file_path": "...",
      "line_range": "...",
      "snippet": "..."
    }
  ],
  "confidence": 0.0-1.0
}
"""


TOOLS = [
    {
        "name": "list_files",
        "description": "List all files in the repo or a subdirectory",
        "input_schema": {
            "type": "object",
            "properties": {
                "subdir": {
                    "type": "string",
                    "description": "Subdirectory to list, default '.'",
                },
            },
        },
    },
    {
        "name": "read_file",
        "description": "Read a file's contents",
        "input_schema": {
            "type": "object",
            "properties": {
                "rel_path": {
                    "type": "string",
                    "description": "Relative file path",
                },
            },
            "required": ["rel_path"],
        },
    },
    {
        "name": "search_code",
        "description": "Search for a string/pattern in the codebase",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query string",
                },
            },
            "required": ["query"],
        },
    },
    {
        "name": "find_references",
        "description": "Find references to a symbol across the codebase",
        "input_schema": {
            "type": "object",
            "properties": {
                "symbol": {
                    "type": "string",
                    "description": "Symbol name to find",
                },
            },
            "required": ["symbol"],
        },
    },
]


MAX_ITERATIONS = 10


def run(repo_id: str, question: str, trace_callback=None) -> Claim:
    messages = [
        {
            "role": "user",
            "content": question,
        }
    ]

    response = None

    for _ in range(MAX_ITERATIONS):

        # -----------------------------------------------------
        # ASK LLM
        # -----------------------------------------------------
        response = chat(
            messages,
            system=SYSTEM,
            tools=TOOLS,
        )

        # -----------------------------------------------------
        # CHECK TOOL CALLS
        # -----------------------------------------------------
        tool_calls = extract_tool_calls(response)

        if not tool_calls:
            break

        # -----------------------------------------------------
        # PRESERVE ASSISTANT MESSAGE
        # -----------------------------------------------------
        assistant_message = response["choices"][0]["message"]

        messages.append({
            "role": "assistant",
            "content": assistant_message.get("content", "") or "",
            **(
                {
                    "tool_calls": assistant_message["tool_calls"]
                }
                if assistant_message.get("tool_calls")
                else {}
            ),
        })

        # -----------------------------------------------------
        # EXECUTE TOOLS
        # -----------------------------------------------------
        for tc in tool_calls:

            if trace_callback:
                trace_callback(
                    "tool_call",
                    agent="code_agent",
                    tool=tc["name"],
                    input=tc["input"],
                )

            try:
                result = call_tool(
                    tc["name"],
                    repo_id=repo_id,
                    **tc["input"],
                )

                result_str = (
                    json.dumps(result)
                    if not isinstance(result, str)
                    else result
                )

            except Exception as e:
                result_str = f"Error: {e}"

            if trace_callback:
                trace_callback(
                    "tool_result",
                    agent="code_agent",
                    tool=tc["name"],
                    output=result_str[:500],
                )

            # -------------------------------------------------
            # ADD TOOL RESULT
            # -------------------------------------------------
            messages.append({
                "role": "tool",
                "tool_call_id": tc["id"],
                "content": result_str,
            })

    # ---------------------------------------------------------
    # EXTRACT FINAL TEXT
    # ---------------------------------------------------------
    text = extract_text(response)

    # ---------------------------------------------------------
    # PARSE CLAIM JSON
    # ---------------------------------------------------------
    try:
        data = json.loads(strip_json_fences(text))

        return Claim(
            text=data.get("text", text),
            evidence=[
                EvidenceItem(**e)
                for e in data.get("evidence", [])
            ],
            confidence=data.get("confidence", 0.5),
        )

    except Exception:
        # Give the model one chance to fix its formatting before giving up.
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
            return Claim(
                text=text,
                evidence=[],
                confidence=0.3,
            )