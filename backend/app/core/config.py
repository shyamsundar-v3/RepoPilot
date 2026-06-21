
from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # OmniRoute local gateway — OpenAI-compatible endpoint (no key required for free providers)
    omniroute_base_url: str = "http://localhost:20128/v1"
    omniroute_api_key: str = "omniroute"  # OmniRoute accepts any non-empty key

    github_token: str = ""

    # ChromaDB telemetry suppression
    anonymized_telemetry: bool = False
    chroma_telemetry: bool = False

    # Heavy model — used by code_agent and git_agent (multi-turn tool use)
    llm_model: str = "auto"
    # Lite model — used by docs_agent, reviewer, planner (simple structured tasks)
    llm_model_lite: str = "auto"

    data_dir: Path = Path(__file__).resolve().parent.parent / "data"

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }

    @property
    def repos_dir(self) -> Path:
        return self.data_dir / "repos"

    @property
    def chroma_dir(self) -> Path:
        return self.data_dir / "chroma"

    @property
    def reports_dir(self) -> Path:
        return self.data_dir / "reports"


settings = Settings()

