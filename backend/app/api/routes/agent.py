from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app.core.config import Settings, get_settings
from app.services.agent_client import AgentChatRequest, AgentClient, AgentNotConfiguredError

router = APIRouter(prefix="/api/agent", tags=["agent"])


def get_agent_client(settings: Settings = Depends(get_settings)) -> AgentClient:
    return AgentClient(settings)


@router.get("/status")
def agent_status(client: AgentClient = Depends(get_agent_client)) -> dict:
    return {"configured": client.is_configured}


@router.post("/chat")
async def agent_chat(
    payload: AgentChatRequest, client: AgentClient = Depends(get_agent_client)
) -> dict:
    try:
        reply = await client.send_message(payload)
    except AgentNotConfiguredError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return reply.model_dump()
