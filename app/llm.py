"""LLM client for the bank complaint triage service.

This version uses only a live LLM backend and removes the offline stub logic.
The model decides the output, while the app validates the returned JSON against the
service contract in app.models.
"""

from __future__ import annotations

import os

from dotenv import load_dotenv

load_dotenv()

PROMPT_VERSION = "triage-v2"

SYSTEM_PROMPT = (
    "You triage bank complaints. Reply with a single JSON object only; do not use Markdown fences. "
    'Include all five keys every time, using this structure: {"category": "...", "priority": 1, '
    '"team": "...", "summary": "...", "needs_human": false}. '
    "Use exactly these fields and no others: "
    'category (one of "card_dispute", "fraud", "account_access", "charges", "other"), '
    "priority (integer 1-4, 1 = most urgent), "
    'team (one of "disputes", "fraud_ops", "digital_support", "branch_services", "human_review"), '
    "summary (at most 200 characters, no account numbers), "
    "needs_human (boolean). Route clear complaints to the best-matching team and set needs_human to false. "
    "If the complaint is too ambiguous or lacks enough information to classify reliably, set category to "
    '"other", team to "human_review", and needs_human to true. Use human_review for cases that cannot be '
    "safely routed to one of the specialist teams. Keep the summary concise and factual."
)


class LiveLLM:
    """A real model through an OpenAI-compatible endpoint."""

    name = "live"

    def __init__(self):
        from openai import AsyncOpenAI

        self.model = os.environ.get("LLM_MODEL", "gemma3:1b")
        self._client = AsyncOpenAI(
            api_key="ollama",
            base_url=os.environ.get("LLM_BASE_URL", "http://localhost:11434/v1"),
            timeout=int(os.environ.get("TRIAGE_TIMEOUT_S", 30)),
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
            response_format={"type": "json_object"},
        )
        return resp.choices[0].message.content or ""


def get_llm():
    """Return the live LLM client."""
    return LiveLLM()