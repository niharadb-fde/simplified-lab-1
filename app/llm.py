"""LLM client for the bank complaint triage service.

This version uses only a live LLM backend and removes the offline stub logic.
The model decides the output, while the app validates the returned JSON against the
service contract in app.models.
"""

from __future__ import annotations

import os

from dotenv import load_dotenv

load_dotenv()

PROMPT_VERSION = "triage-v1"

SYSTEM_PROMPT = (
    "You triage bank complaints. Reply with JSON only, with keys: "
    'category (one of "card_dispute", "fraud", "account_access", "charges", "other"), '
    "priority (integer 1-4, 1 = most urgent), "
    'team (one of "disputes", "fraud_ops", "digital_support", "branch_services"), '
    "summary (at most 200 characters, no account numbers)."
)


class LiveLLM:
    """A real model through an OpenAI-compatible endpoint."""

    name = "live"

    def __init__(self):
        api_key = os.environ.get("LLM_API_KEY") or os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError("Set LLM_API_KEY or GEMINI_API_KEY before using the live LLM.")

        from openai import AsyncOpenAI

        self.model = os.environ.get("LLM_MODEL", "gemini-3.8-flash")
        self._client = AsyncOpenAI(
            api_key=api_key,
            base_url=os.environ.get("LLM_BASE_URL", "https://generativelanguage.googleapis.com/v1beta/openai/"),
            timeout=10,
            max_retries=1,
        )

    async def complete(self, complaint_id: str, text: str) -> str:
        del complaint_id  # Not needed by the live model call.
        resp = await self._client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": text},
            ],
            temperature=0,
        )
        return resp.choices[0].message.content or ""


def get_llm():
    """Return the live LLM client."""
    return LiveLLM()