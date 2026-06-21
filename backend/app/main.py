import logging
import os

# ── ChromaDB telemetry suppression (3-layer fix) ─────────────────────────────
# Layer 1: env vars — tell ChromaDB settings object to disable telemetry
os.environ["ANONYMIZED_TELEMETRY"] = "False"
os.environ["CHROMA_TELEMETRY"] = "False"

# Layer 2: monkey-patch posthog — ChromaDB 0.6.x calls posthog.capture() with
# 3 positional args but the installed posthog version only accepts keyword args,
# causing "capture() takes 1 positional argument but 3 were given".
# Replace the whole posthog module's send functions with silent no-ops.
try:
    import posthog as _posthog
    _posthog.disabled = True
    _posthog.capture = lambda *a, **kw: None
    _posthog.identify = lambda *a, **kw: None
    _posthog.flush = lambda *a, **kw: None
except Exception:
    pass

# Layer 3: silence the chromadb telemetry logger so any residual log lines
# (e.g. from other threads) don't pollute stdout.
logging.getLogger("chromadb.telemetry.product.posthog").setLevel(logging.CRITICAL)
logging.getLogger("chromadb.telemetry").setLevel(logging.CRITICAL)
# ─────────────────────────────────────────────────────────────────────────────

import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.analyze import router as analyze_router
from app.api.report import router as report_router
from app.api.chat import router as chat_router
from app.api.trace_ws import router as trace_ws_router
from app.core.config import settings

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def _models_url() -> str:
    """Build the OmniRoute /v1/models URL safely.

    NOTE: str.rstrip('/v1') strips any trailing characters in the set
    {'/', 'v', '1'} -- NOT the literal suffix "/v1" -- so it can eat
    extra characters (e.g. a port ending in "1") depending on the
    configured base URL. Use removesuffix for an exact match instead.
    """
    base = settings.omniroute_base_url.rstrip("/")
    base = base.removesuffix("/v1")
    return f"{base}/v1/models"


app = FastAPI(title="RepoPilot", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(analyze_router)
app.include_router(report_router)
app.include_router(chat_router)
app.include_router(trace_ws_router)


@app.on_event("startup")
async def check_omniroute():
    """Warn at startup if OmniRoute is not reachable."""
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.get(_models_url())
            if resp.is_success:
                logger.info("[OK] OmniRoute is reachable at %s", settings.omniroute_base_url)
            else:
                logger.warning(
                    "[WARN] OmniRoute responded with status %d at %s. "
                    "Requests may fail.", resp.status_code, settings.omniroute_base_url
                )
    except Exception:
        logger.warning(
            "[WARN] OmniRoute is NOT running at %s. "
            "Start it with: omniroute   (npm install -g omniroute)",
            settings.omniroute_base_url,
        )


@app.get("/health")
async def health():
    omniroute_status = "unknown"
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.get(_models_url())
            omniroute_status = "ok" if resp.is_success else f"error:{resp.status_code}"
    except Exception:
        omniroute_status = "not_running"
    return {
        "status": "ok",
        "llm_gateway": settings.omniroute_base_url,
        "omniroute": omniroute_status,
    }