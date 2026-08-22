"""Client for the Upstage Studio document-check Agent.

This is the concrete, already-deployed Upstage agent used by the real
"Upload document" flow on the dashboard (FS-08/FS-10 in spirit — classify
+ check completeness of one uploaded document). It is unrelated to
app/services/agent_client.py, which is a stub for a *different*, not-yet-
deployed chat agent another teammate is building.

Flow (per Upstage's documented contract):
  1. POST /v2/files          (multipart upload) -> file_id
  2. POST /v2/responses      (model=agent id, input references file_id) -> job
  3. GET  /v2/responses/{id} (poll until completed/failed)
  4. json.loads(output_text) -> {"result": bool, "How to fix": str}

The agent's actual response key casing/spacing ("How to fix") is honored
literally, but parsing here tolerates a few reasonable variants so a small
prompt change on the Studio side doesn't silently break this integration.

In practice this Studio agent ignores that documented JSON contract and
instead free-associates a multi-section Korean markdown review (see the
"Caveat" section of README.md). Since we can't change its Studio config,
_INSTRUCTION below is sent as an accompanying input_text block asking it,
in plain language, to answer in a specific two-line English format
instead. The agent reliably follows this even though it never emits the
originally documented JSON — see _parse_output for how each shape is
handled, documented-JSON first, then this instructed format, then a raw-
text fallback if the agent ever ignores instructions entirely.
"""

from __future__ import annotations

import asyncio
import json
import re
from dataclasses import dataclass
from typing import Any, Optional

import httpx

_CITATION_MARKER = re.compile(r"【[^】]*】")


def _clean_markdown(text: str) -> str:
    return _CITATION_MARKER.sub("", text).strip()

UPSTAGE_BASE_URL = "https://api.upstage.ai/v2"
UPSTAGE_AGENT_MODEL = "agt_Qo9QXjejSgT6TZ3Z5MR8q2"

POLL_INTERVAL_SECONDS = 2
POLL_TIMEOUT_SECONDS = 90

RESULT_KEYS = ("result", "passed", "is_valid", "valid")
FIX_KEYS = ("How to fix", "how_to_fix", "howToFix", "suggested_fix", "fix")

_INSTRUCTION = (
    "Reply only in English, in this exact two-part format:\n"
    "Line 1: the single word PASS if the document is acceptable with nothing "
    "missing, unreadable, or wrong, or NEEDS_FIX if it is not.\n"
    "Line 2 (only if NEEDS_FIX): 1-3 short sentences explaining only why it "
    "needs to be corrected or re-uploaded. Omit line 2 entirely if PASS.\n"
    "Do not include a full itemized review or general visa requirements list."
)


class UpstageAgentError(RuntimeError):
    pass


class UpstageAgentNotConfiguredError(UpstageAgentError):
    pass


class UpstageAgentTimeoutError(UpstageAgentError):
    pass


@dataclass
class DocumentCheckResult:
    passed: bool
    how_to_fix: Optional[str]
    raw: Any


def _extract(data: dict, keys: tuple) -> Any:
    for key in keys:
        if key in data:
            return data[key]
    return None


class UpstageDocumentAgent:
    def __init__(self, api_key: Optional[str]) -> None:
        self._api_key = api_key

    @property
    def is_configured(self) -> bool:
        return bool(self._api_key)

    def _headers(self) -> dict:
        return {"Authorization": f"Bearer {self._api_key}"}

    async def check_document(
        self, content: bytes, filename: str, content_type: str
    ) -> DocumentCheckResult:
        if not self.is_configured:
            raise UpstageAgentNotConfiguredError(
                "UPSTAGE_API_KEY is not set (see backend/.env.example)."
            )

        async with httpx.AsyncClient(base_url=UPSTAGE_BASE_URL, timeout=60) as client:
            file_id = await self._upload_file(client, content, filename, content_type)
            job = await self._create_job(client, file_id)
            job = await self._poll_job(client, job["id"])

        if job.get("status") != "completed":
            raise UpstageAgentError(f"Upstage job did not complete (status={job.get('status')})")

        output_text = job.get("output_text")
        if not output_text:
            output_text = self._extract_output_text(job)

        return self._parse_output(output_text)

    def _parse_output(self, output_text: Optional[str]) -> DocumentCheckResult:
        """Parse the agent's output_text into a pass/fail + explanation.

        Tries three shapes, most-trustworthy first:
        1. The originally documented JSON object: {"result": bool, "How to
           fix": str}, in case the Studio config is ever changed to match it.
        2. The PASS / NEEDS_FIX two-line format requested by _INSTRUCTION,
           which is what the live agent actually reliably produces.
        3. Anything else: treated as `needs_review` with the raw text as the
           explanation, rather than guessing pass/fail out of prose — never
           invent confidence DragonPath doesn't have (D-08 Safety Rules).
        """
        if not output_text:
            raise UpstageAgentError("Upstage agent returned an empty response")

        parsed: Any
        try:
            parsed = json.loads(output_text)
        except json.JSONDecodeError:
            parsed = output_text

        # A JSON-encoded string decodes to `str` — unwrap it once more in
        # case the underlying text is itself a JSON object.
        if isinstance(parsed, str):
            try:
                parsed = json.loads(parsed)
            except json.JSONDecodeError:
                pass

        if isinstance(parsed, dict):
            result = _extract(parsed, RESULT_KEYS)
            how_to_fix = _extract(parsed, FIX_KEYS)
            return DocumentCheckResult(
                passed=bool(result),
                how_to_fix=str(how_to_fix) if how_to_fix else None,
                raw=parsed,
            )

        free_text = _clean_markdown(parsed if isinstance(parsed, str) else output_text)
        first_line, _, rest = free_text.partition("\n")

        if first_line.strip().upper().startswith("PASS"):
            return DocumentCheckResult(passed=True, how_to_fix=None, raw=output_text)

        if first_line.strip().upper().startswith("NEEDS_FIX"):
            return DocumentCheckResult(
                passed=False, how_to_fix=rest.strip() or None, raw=output_text
            )

        return DocumentCheckResult(passed=False, how_to_fix=free_text, raw=output_text)

    async def _upload_file(
        self, client: httpx.AsyncClient, content: bytes, filename: str, content_type: str
    ) -> str:
        response = await client.post(
            "/files",
            headers=self._headers(),
            files={"file": (filename, content, content_type or "application/octet-stream")},
            data={"purpose": "user_data"},
        )
        response.raise_for_status()
        return response.json()["id"]

    async def _create_job(self, client: httpx.AsyncClient, file_id: str) -> dict:
        response = await client.post(
            "/responses",
            headers={**self._headers(), "Content-Type": "application/json"},
            json={
                "model": UPSTAGE_AGENT_MODEL,
                "include": ["last"],
                "input": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "input_text", "text": _INSTRUCTION},
                            {"type": "input_file", "file_id": file_id},
                        ],
                    }
                ],
            },
        )
        response.raise_for_status()
        return response.json()

    async def _poll_job(self, client: httpx.AsyncClient, job_id: str) -> dict:
        elapsed = 0
        while elapsed <= POLL_TIMEOUT_SECONDS:
            response = await client.get(
                f"/responses/{job_id}",
                headers=self._headers(),
                params={"include[]": "last"},
            )
            response.raise_for_status()
            job = response.json()
            if job.get("status") in ("completed", "failed"):
                return job
            await asyncio.sleep(POLL_INTERVAL_SECONDS)
            elapsed += POLL_INTERVAL_SECONDS

        raise UpstageAgentTimeoutError(f"Upstage job {job_id} did not finish in time")

    def _extract_output_text(self, job: dict) -> Optional[str]:
        for item in job.get("output", []):
            for content in item.get("content", []):
                if content.get("type") == "output_text":
                    return content.get("text")
        return None
