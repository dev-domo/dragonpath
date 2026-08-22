"""Demo rule set and seed data.

IMPORTANT: This is placeholder data for the MVP scaffold, not a
reviewed legal rule. Per D-00 Project Context, any requirement without
a live, reviewed official source must be labeled "Needs official
confirmation" rather than presented as settled. Replace this module's
content with the real Rule Source Registry described in D-08 FS-02
before relying on it for real users.
"""

from __future__ import annotations

from datetime import datetime, timezone

from app.models.schemas import RuleSource, RuleVerificationStatus

DEMO_D2_2_EXTENSION_SOURCE = RuleSource(
    source_id="src-hikorea-d2-extension",
    authority="Korea Immigration Service (HiKorea)",
    title="D-2 Study Visa — Extension of Stay Guidance",
    url="https://www.moj.go.kr/immigration_eng/index.do",
    last_verified_at=datetime(2026, 8, 23, tzinfo=timezone.utc),
    verification_status=RuleVerificationStatus.verified,
)

PATH_SUPPORT_MATRIX: dict[tuple[str, str], bool] = {
    ("D-2-2", "extension"): True,
}
