"""Model provider factory.

Every agent asks for a *role*, never a concrete model. Which provider backs a
role is a deployment decision, kept here so that switching between the
Anthropic API, Bedrock and a local Ollama model is a config change rather than
a code change.

Configure with environment variables (a .env file next to the repo root is
loaded automatically):

    KSA_PROVIDER   anthropic (default) | bedrock | ollama
    KSA_MODEL_FAST     override the model behind the "fast" role
    KSA_MODEL_REASONING override the model behind the "reasoning" role

Provider-specific:
    ANTHROPIC_API_KEY   required when KSA_PROVIDER=anthropic
    AWS_PROFILE_KSA     AWS profile for bedrock; never falls back to `default`
    AWS_REGION_KSA      AWS region for bedrock (default us-west-2)
    OLLAMA_HOST         default http://localhost:11434
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Literal

from strands.models.model import Model

Role = Literal["fast", "reasoning"]

_DEFAULTS: dict[str, dict[Role, str]] = {
    "anthropic": {
        "fast": "claude-haiku-4-5-20251001",
        "reasoning": "claude-sonnet-5",
    },
    "bedrock": {
        "fast": "us.anthropic.claude-haiku-4-5-20251001-v1:0",
        "reasoning": "global.anthropic.claude-sonnet-5",
    },
    "ollama": {
        "fast": "llama3.2",
        "reasoning": "llama3.1:8b",
    },
}

_ENV_OVERRIDE: dict[Role, str] = {
    "fast": "KSA_MODEL_FAST",
    "reasoning": "KSA_MODEL_REASONING",
}


def _load_dotenv() -> None:
    """Minimal .env loader; avoids a dependency for two variables."""
    env_path = Path(__file__).resolve().parents[2] / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip().strip("'\""))


def resolve_model_id(role: Role, provider: str) -> str:
    override = os.getenv(_ENV_OVERRIDE[role])
    if override:
        return override
    return _DEFAULTS[provider][role]


def build_model(role: Role = "reasoning", *, max_tokens: int = 4096) -> Model:
    """Return a Strands model for the given role under the active provider."""
    _load_dotenv()
    provider = os.getenv("KSA_PROVIDER", "anthropic").lower()
    if provider not in _DEFAULTS:
        raise ValueError(
            f"Unknown KSA_PROVIDER {provider!r}; expected one of "
            f"{', '.join(sorted(_DEFAULTS))}"
        )
    model_id = resolve_model_id(role, provider)

    if provider == "anthropic":
        from strands.models.anthropic import AnthropicModel

        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise RuntimeError(
                "ANTHROPIC_API_KEY is not set. Put it in a .env file at the "
                "repo root or export it, or set KSA_PROVIDER to bedrock/ollama."
            )
        return AnthropicModel(
            client_args={"api_key": api_key},
            model_id=model_id,
            max_tokens=max_tokens,
        )

    if provider == "bedrock":
        import boto3
        from strands.models import BedrockModel

        # Deliberately not falling back to the `default` profile: on this
        # machine `default` points at an account that must not be billed for
        # this project.
        profile = os.getenv("AWS_PROFILE_KSA")
        if not profile:
            raise RuntimeError(
                "AWS_PROFILE_KSA must name the AWS profile to use. Refusing to "
                "fall back to the default profile."
            )
        session = boto3.Session(
            profile_name=profile,
            region_name=os.getenv("AWS_REGION_KSA", "us-west-2"),
        )
        return BedrockModel(
            boto_session=session, model_id=model_id, max_tokens=max_tokens
        )

    from strands.models.ollama import OllamaModel

    return OllamaModel(
        host=os.getenv("OLLAMA_HOST", "http://localhost:11434"),
        model_id=model_id,
        max_tokens=max_tokens,
    )


def active_provider() -> str:
    _load_dotenv()
    return os.getenv("KSA_PROVIDER", "anthropic").lower()
