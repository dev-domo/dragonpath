"""Client for the external Upstage-based Agent service.

That service is being built by another team member and is not part of
this repo. Rather than guess at its real contract, this client defines
the minimal interface DragonPath needs from it and talks over plain
HTTP + bearer auth, which is the lowest-common-denominator most agent
services (including Upstage's own OpenAI-compatible Solar API) expose.

When the real agent is ready:
1. Set AGENT_BASE_URL and AGENT_API_KEY in backend/.env.
2. If its request/response shape differs from `AgentChatRequest` /
   `AgentChatReply` below, adjust `send_message` to match — everything
   upstream of this module (the /api/agent route, the frontend) only
   depends on those two shapes, not on Upstage's wire format.
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel

import httpx

from app.core.config import Settings


class AgentNotConfiguredError(RuntimeError):
    pass


class AgentChatMessage(BaseModel):
    role: str  # "user" | "assistant" | "system"
    content: str


class AgentChatRequest(BaseModel):
    case_id: Optional[str] = None
    messages: list[AgentChatMessage]


class AgentChatReply(BaseModel):
    reply: str
    raw: Optional[dict] = None


class AgentClient:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    @property
    def is_configured(self) -> bool:
        return bool(self._settings.agent_base_url)

    async def send_message(self, request: AgentChatRequest) -> AgentChatReply:
        if not self.is_configured:
            raise AgentNotConfiguredError(
                "AGENT_BASE_URL is not set. Point it at the Upstage agent "
                "service once it is deployed (see backend/.env.example)."
            )

        headers = {}
        if self._settings.agent_api_key:
            headers["Authorization"] = f"Bearer {self._settings.agent_api_key}"

        async with httpx.AsyncClient(base_url=self._settings.agent_base_url, timeout=30) as client:
            response = await client.post(
                "/chat",
                json=request.model_dump(),
                headers=headers,
            )
            response.raise_for_status()
            data = response.json()

        return AgentChatReply(reply=data.get("reply", ""), raw=data)
