from __future__ import annotations

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from app.core.config import Settings, get_settings
from app.models.schemas import OnboardingRequest, ReadinessSummary, VisaCase
from app.services.readiness import compute_readiness
from app.services.store import InvalidTransitionError, store
from app.services.upstage_document_agent import (
    UpstageAgentError,
    UpstageAgentNotConfiguredError,
    UpstageDocumentAgent,
)

router = APIRouter(prefix="/api/cases", tags=["cases"])

MAX_UPLOAD_BYTES = 20 * 1024 * 1024  # 20MB — Upstage allows up to 500MB; kept small for the demo


def get_document_agent(settings: Settings = Depends(get_settings)) -> UpstageDocumentAgent:
    return UpstageDocumentAgent(settings.upstage_api_key)


@router.post("", response_model=VisaCase)
def create_case(payload: OnboardingRequest) -> VisaCase:
    return store.create_case(payload)


@router.get("/{case_id}", response_model=VisaCase)
def get_case(case_id: str) -> VisaCase:
    case = store.get_case(case_id)
    if case is None:
        raise HTTPException(status_code=404, detail="Visa case not found")
    return case


@router.get("/{case_id}/readiness", response_model=ReadinessSummary)
def get_readiness(case_id: str) -> ReadinessSummary:
    case = store.get_case(case_id)
    if case is None:
        raise HTTPException(status_code=404, detail="Visa case not found")
    return compute_readiness(case)


@router.post("/{case_id}/checklist/{item_id}/check", response_model=VisaCase)
def check_item_manually(case_id: str, item_id: str) -> VisaCase:
    """The gray -> blue manual check: hand-confirm a pending item, or
    override a flagged one. Reversible with /uncheck as long as no
    document was uploaded for the item.
    """
    if store.get_case(case_id) is None:
        raise HTTPException(status_code=404, detail="Visa case not found")
    try:
        return store.mark_item_checked_manually(case_id, item_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Checklist item not found")
    except InvalidTransitionError as exc:
        raise HTTPException(status_code=409, detail=str(exc))


@router.post("/{case_id}/checklist/{item_id}/uncheck", response_model=VisaCase)
def uncheck_item_manually(case_id: str, item_id: str) -> VisaCase:
    """The blue -> gray undo. Only reverses a hand-confirmed check; an
    item completed by a checked document returns 409.
    """
    if store.get_case(case_id) is None:
        raise HTTPException(status_code=404, detail="Visa case not found")
    try:
        return store.uncheck_item_manually(case_id, item_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Checklist item not found")
    except InvalidTransitionError as exc:
        raise HTTPException(status_code=409, detail=str(exc))


@router.post("/{case_id}/checklist/{item_id}/upload")
async def upload_document(
    case_id: str,
    item_id: str,
    file: UploadFile = File(...),
    agent: UpstageDocumentAgent = Depends(get_document_agent),
) -> dict:
    """FS-07..FS-10 collapsed into one call for the MVP: upload the file,
    run it through the Upstage document-check Agent, and update the
    matching checklist item / document / issue based on the result.
    """
    if store.get_case(case_id) is None:
        raise HTTPException(status_code=404, detail="Visa case not found")

    content = await file.read()
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="File is larger than the 20MB demo limit.")

    try:
        result = await agent.check_document(
            content, file.filename or "document", file.content_type or ""
        )
    except UpstageAgentNotConfiguredError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except UpstageAgentError as exc:
        raise HTTPException(
            status_code=502, detail=f"DragonPath could not check this document: {exc}"
        ) from exc

    try:
        case, item, issue = store.apply_document_check(
            case_id, item_id, file.filename or "document", result
        )
    except KeyError:
        raise HTTPException(status_code=404, detail="Checklist item not found")
    except InvalidTransitionError as exc:
        raise HTTPException(status_code=409, detail=str(exc))

    return {
        "case": case,
        "passed": result.passed,
        "issue_id": issue.issue_id if issue else None,
    }
