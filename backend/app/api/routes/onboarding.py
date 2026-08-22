from __future__ import annotations

from fastapi import APIRouter

from app.data.seed import DEMO_D2_2_EXTENSION_SOURCE, PATH_SUPPORT_MATRIX
from app.models.schemas import OnboardingRequest, PathReviewResult, PathReviewStep

router = APIRouter(prefix="/api/onboarding", tags=["onboarding"])


@router.post("/path-review", response_model=PathReviewResult)
def review_path(payload: OnboardingRequest) -> PathReviewResult:
    """FS-01 path routing: only ever returns a checklist preview for
    paths present in PATH_SUPPORT_MATRIX. Everything else comes back
    unsupported so the frontend can show the "not yet supported" state
    (D-09 7.5) instead of a fabricated checklist.
    """
    key = (payload.current_visa_type, payload.application_action.value)
    supported = PATH_SUPPORT_MATRIX.get(key, False)

    if not supported:
        return PathReviewResult(
            supported=False,
            path_label_en=f"{payload.current_visa_type} → {payload.application_action.value}",
            description_en="This visa path is not yet supported.",
            onboarding=payload,
            unsupported_reason_en=(
                "DragonPath will not generate an unverified checklist. "
                "Please confirm the current requirements through HiKorea "
                "or the Immigration Contact Center (1345)."
            ),
        )

    return PathReviewResult(
        supported=True,
        path_label_en=f"{payload.current_visa_type} → Extend {payload.current_visa_type}",
        description_en="We matched your answers to a verified rule set for this visa path.",
        rule_source=DEMO_D2_2_EXTENSION_SOURCE,
        preview_steps=[
            PathReviewStep(step_number=1, label_en="Review your source-backed requirements"),
            PathReviewStep(step_number=2, label_en="Prepare and upload the required documents"),
            PathReviewStep(step_number=3, label_en="Resolve missing fields and inconsistencies"),
        ],
        onboarding=payload,
    )
