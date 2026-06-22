import json
import logging
import subprocess
import threading
import time

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

# OmniRoute — local OpenAI-compatible gateway (auto-routes across 350+ providers)
# Dashboard: http://localhost:20128
# Docs: omniroute.md in project root

MAX_RETRIES_RATE_LIMIT = 5
MAX_RETRIES_SERVER_ERROR = 3
MAX_WAIT_SECONDS = 60

_client: httpx.Client | None = None
_client_lock = threading.Lock()


def _get_client() -> httpx.Client:
    global _client

    # Sections now run concurrently on multiple threads, so guard
    # lazy-init/reset of the shared client to avoid creating (and leaking)
    # more than one httpx.Client when several threads race here at once.
    if _client is None:
        with _client_lock:
            if _client is None:
                _client = httpx.Client(
                    base_url=settings.omniroute_base_url,
                    headers={
                        "Authorization": f"Bearer {settings.omniroute_api_key}",
                        "Content-Type": "application/json",
                    },
                    timeout=120.0,
                )

    return _client


def _reset_client() -> None:
    """Force recreation of the HTTP client (useful after config changes)."""
    global _client
    with _client_lock:
        if _client is not None:
            _client.close()
            _client = None


def _compute_retry_wait(resp: httpx.Response, attempt: int) -> float:
    """Compute how long to wait before retrying, using rate-limit reset
    header when available, otherwise exponential backoff."""
    reset_ms = resp.headers.get("X-RateLimit-Reset") or resp.headers.get("x-ratelimit-reset")
    if reset_ms:
        try:
            reset_time = int(reset_ms) / 1000  # header is in milliseconds
            wait = max(reset_time - time.time(), 1.0)
            return min(wait, MAX_WAIT_SECONDS)
        except (ValueError, TypeError):
            pass
    # Exponential backoff: 2, 4, 8, 16, ...
    return min(2 ** attempt, MAX_WAIT_SECONDS)


def chat(
    messages: list[dict],
    system: str = "",
    tools: list[dict] | None = None,
    max_tokens: int = 4096,
    model: str | None = None,
) -> dict:
    """
    Send a chat request to OmniRoute (local OpenAI-compatible gateway).
    Returns the raw JSON response as a dictionary.

    OmniRoute auto-routes across 350+ providers and handles fallback transparently.
    Use model="auto" (default) for smart routing, or any specific model ID.

    Args:
        messages:   Conversation history in internal format.
        system:     Optional system prompt.
        tools:      Optional list of tool definitions.
        max_tokens: Maximum tokens to generate.
        model:      Model to request. Defaults to settings.llm_model ("auto").
                    Pass settings.llm_model_lite for lightweight structured tasks.

    Retries automatically on 429 rate-limit and 5xx server errors.
    OmniRoute's own circuit-breaker layer also handles provider-level fallback.
    """

    client = _get_client()
    resolved_model = model or settings.llm_model

    oai_messages = []

    # ---------------------------------------------------------
    # SYSTEM MESSAGE
    # ---------------------------------------------------------
    if system:
        oai_messages.append({
            "role": "system",
            "content": system,
        })

    # ---------------------------------------------------------
    # CONVERT MESSAGES TO OPENAI FORMAT
    # ---------------------------------------------------------
    for msg in messages:
        role = msg.get("role")
        content = msg.get("content", "")

        # -----------------------------------------------------
        # ASSISTANT MESSAGE
        # -----------------------------------------------------
        if role == "assistant":
            entry = {
                "role": "assistant",
                "content": content if isinstance(content, str) else "",
            }

            # Preserve OpenAI-style tool_calls
            if msg.get("tool_calls"):
                entry["tool_calls"] = msg["tool_calls"]

            oai_messages.append(entry)

        # -----------------------------------------------------
        # TOOL RESULT MESSAGE
        # -----------------------------------------------------
        elif role == "tool":
            oai_messages.append({
                "role": "tool",
                "tool_call_id": msg["tool_call_id"],
                "content": (
                    content
                    if isinstance(content, str)
                    else json.dumps(content)
                ),
            })

        # -----------------------------------------------------
        # OLD INTERNAL TOOL RESULT FORMAT (list of tool_result blocks)
        # -----------------------------------------------------
        elif (
            role == "user"
            and isinstance(content, list)
        ):
            converted = False

            for block in content:
                if (
                    isinstance(block, dict)
                    and block.get("type") == "tool_result"
                ):
                    oai_messages.append({
                        "role": "tool",
                        "tool_call_id": block["tool_use_id"],
                        "content": (
                            block["content"]
                            if isinstance(block["content"], str)
                            else json.dumps(block["content"])
                        ),
                    })
                    converted = True

            # If it wasn't a tool-result block, preserve as normal
            if not converted:
                oai_messages.append({
                    "role": role,
                    "content": json.dumps(content),
                })

        # -----------------------------------------------------
        # NORMAL USER MESSAGE
        # -----------------------------------------------------
        else:
            oai_messages.append({
                "role": role,
                "content": (
                    content
                    if isinstance(content, str)
                    else json.dumps(content)
                ),
            })

    # ---------------------------------------------------------
    # REQUEST BODY
    # ---------------------------------------------------------
    body = {
        "model": resolved_model,
        "max_tokens": max_tokens,
        "messages": oai_messages,
        "stream": False,  # Force non-streaming response — OmniRoute defaults to SSE streaming
    }

    # ---------------------------------------------------------
    # TOOLS
    # ---------------------------------------------------------
    if tools:
        oai_tools = []

        for t in tools:
            oai_tools.append({
                "type": "function",
                "function": {
                    "name": t["name"],
                    "description": t.get("description", ""),
                    "parameters": t.get(
                        "input_schema",
                        {
                            "type": "object",
                            "properties": {},
                        },
                    ),
                },
            })

        body["tools"] = oai_tools

    # ---------------------------------------------------------
    # CALL OMNIROUTE (with retry)
    # OmniRoute handles provider-level fallback internally;
    # we still retry on 429/5xx in case the whole gateway is
    # temporarily overloaded.  We also retry ConnectError in
    # case OmniRoute takes a moment to start.
    # ---------------------------------------------------------
    resp = None
    MAX_CONNECT_RETRIES = 3

    for attempt in range(MAX_RETRIES_RATE_LIMIT + 1):
        # ── Connection attempt (with ConnectError retry) ─────────────────
        for conn_attempt in range(MAX_CONNECT_RETRIES):
            try:
                client = _get_client()  # re-fetch in case client was reset
                resp = client.post("chat/completions", json=body)
                break  # connected successfully
            except httpx.ConnectError as ce:
                _reset_client()  # discard stale socket
                wait = 3 * (conn_attempt + 1)
                logger.warning(
                    "Cannot connect to OmniRoute at %s (attempt %d/%d). "
                    "Is OmniRoute running? Start it with: omniroute  — retrying in %ds",
                    settings.omniroute_base_url, conn_attempt + 1, MAX_CONNECT_RETRIES, wait,
                )
                if conn_attempt + 1 >= MAX_CONNECT_RETRIES:
                    raise RuntimeError(
                        f"OmniRoute is not reachable at {settings.omniroute_base_url}. "
                        f"Start it first with: omniroute"
                    ) from ce
                time.sleep(wait)
        # ─────────────────────────────────────────────────────────────────

        # Success
        if resp.is_success:
            if not resp.content:
                logger.error(
                    "OmniRoute returned 200 OK with empty body (attempt %d). "
                    "Is OmniRoute running at %s? Try: omniroute",
                    attempt + 1, settings.omniroute_base_url,
                )
                raise RuntimeError(
                    f"OmniRoute returned an empty response body (200 OK). "
                    f"Make sure OmniRoute is running at {settings.omniroute_base_url}."
                )
            try:
                return resp.json()
            except Exception as exc:
                logger.error(
                    "OmniRoute response is not valid JSON (status %d). Body: %r",
                    resp.status_code, resp.text[:500],
                )
                raise RuntimeError(
                    f"OmniRoute returned non-JSON response: {resp.text[:500]}"
                ) from exc

        # Rate limit (429) — retry with backoff
        if resp.status_code == 429:
            if attempt >= MAX_RETRIES_RATE_LIMIT:
                break
            wait = _compute_retry_wait(resp, attempt + 1)
            logger.warning(
                "OmniRoute rate limited (429) on model %s. Waiting %.1fs before retry %d/%d",
                resolved_model, wait, attempt + 1, MAX_RETRIES_RATE_LIMIT,
            )
            time.sleep(wait)
            continue

        # Server error (5xx) — retry with backoff
        if resp.status_code >= 500:
            if attempt >= MAX_RETRIES_SERVER_ERROR:
                break
            wait = min(2 ** attempt, MAX_WAIT_SECONDS)
            logger.warning(
                "OmniRoute server error (%d). Waiting %.1fs before retry %d/%d",
                resp.status_code, wait, attempt + 1, MAX_RETRIES_SERVER_ERROR,
            )
            time.sleep(wait)
            continue

        # Other client errors — fail immediately
        break

    logger.error(
        "OmniRoute API failed after all retries. Status: %s  Body: %r",
        resp.status_code if resp is not None else "N/A",
        (resp.text[:500] if resp is not None else ""),
    )
    raise RuntimeError(
        f"OmniRoute API error {resp.status_code if resp is not None else 'N/A'}: "
        f"{resp.text[:500] if resp is not None else ''}"
    )


# =============================================================
# EXTRACT TEXT
# =============================================================

def extract_text(response: dict) -> str:
    """
    Extract normal assistant text from an OpenAI-format response.
    """

    try:
        choice = response["choices"][0]
        message = choice["message"]

        return message.get("content", "") or ""

    except (KeyError, IndexError, TypeError):
        return ""


# =============================================================
# EXTRACT TOOL CALLS
# =============================================================

def extract_tool_calls(response: dict) -> list[dict]:
    """
    Convert OpenAI tool calls into the internal format
    expected by code_agent.py and git_agent.py.
    """

    try:
        choice = response["choices"][0]
        message = choice["message"]

        raw = message.get("tool_calls", []) or []

    except (KeyError, IndexError, TypeError):
        return []

    calls = []

    for tc in raw:
        try:
            fn = tc["function"]

            arguments = fn.get("arguments", "{}")

            if isinstance(arguments, str):
                try:
                    args = json.loads(arguments)
                except json.JSONDecodeError:
                    args = {}
            else:
                args = arguments or {}

            calls.append({
                "id": tc["id"],
                "name": fn["name"],
                "input": args,
            })

        except (KeyError, TypeError):
            continue

    return calls


# =============================================================
# STRIP JSON FENCES
# =============================================================

def strip_json_fences(text: str) -> str:
    """
    Remove markdown code fences that LLMs often wrap around JSON responses:
        ```json\\n{...}\\n```
        ```\\n{...}\\n```

    Returns the cleaned string ready for json.loads().
    """
    import re
    # Strip leading/trailing whitespace first
    text = text.strip()
    # Match ```json ... ``` or ``` ... ``` (including newlines inside)
    pattern = r'^```(?:json)?\s*\n?(.*?)\n?```$'
    match = re.match(pattern, text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return text