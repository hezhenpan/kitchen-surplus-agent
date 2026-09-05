"""Model provider factory.

Every agent asks for a *role*, never a concrete model. Which provider backs a
role is a deployment decision, kept here so that switching between the
Anthropic API, Bedrock and a local Ollama model is a config change rather than
a code change.

Configure with environment variables (a .env file next to the repo root is
loaded automatically):

    KSA_PROVIDER   anthropic (default) | bedrock | glm | ollama
    KSA_MODEL_FAST     override the model behind the "fast" role
    KSA_MODEL_REASONING override the model behind the "reasoning" role

Provider-specific:
    ANTHROPIC_API_KEY   required when KSA_PROVIDER=anthropic
    GLM_API_KEY         required when KSA_PROVIDER=glm
    KSA_BASE_URL        override the Anthropic-compatible endpoint
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
    # Zhipu GLM exposes an Anthropic-compatible endpoint, so it reuses the
    # Anthropic client with a different base_url. Test-phase only: the final
    # submission should run on a provider the judges expect.
    "glm": {
        "fast": "glm-5.3-flash",
        "reasoning": "glm-5.3",
    },
}

# Anthropic-compatible endpoints, keyed by provider.
_BASE_URLS: dict[str, str] = {
    "glm": "https://open.bigmodel.cn/api/anthropic",
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


def build_model(role: Role = "reasoning", *, max_tokens: int = 8192) -> Model:
    """Return a Strands model for the given role under the active provider."""
    _load_dotenv()
    provider = os.getenv("KSA_PROVIDER", "anthropic").lower()
    if provider not in _DEFAULTS:
        raise ValueError(
            f"Unknown KSA_PROVIDER {provider!r}; expected one of "
            f"{', '.join(sorted(_DEFAULTS))}"
        )
    model_id = resolve_model_id(role, provider)

    if provider in ("anthropic", "glm"):
        from strands.models.anthropic import AnthropicModel

        key_var = "ANTHROPIC_API_KEY" if provider == "anthropic" else "GLM_API_KEY"
        api_key = os.getenv(key_var)
        if not api_key:
            raise RuntimeError(
                f"{key_var} is not set. Put it in a .env file at the repo root "
                f"or export it, or set KSA_PROVIDER to another provider."
            )
        client_args: dict[str, str] = {"api_key": api_key}
        base_url = os.getenv("KSA_BASE_URL") or _BASE_URLS.get(provider)
        if base_url:
            client_args["base_url"] = base_url
        return AnthropicModel(
            client_args=client_args,
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
