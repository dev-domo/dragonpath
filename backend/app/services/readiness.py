from __future__ import annotations

from datetime import datetime, timezone

from app.models.schemas import ChecklistItemStatus, DocumentStatus, IssueSeverity, IssueStatus, ReadinessSummary, VisaCase


def compute_readiness(case: VisaCase) -> ReadinessSummary:
    """Implements the FS-16 readiness decision table."""
    required_total = len(case.checklist)
    required_complete = sum(
        1 for item in case.checklist if item.status == ChecklistItemStatus.completed
    )
    documents_total = len(case.documents)
    documents_verified = sum(
        1 for doc in case.documents if doc.status == DocumentStatus.verified
    )
    open_critical = sum(
        1
        for issue in case.issues
        if issue.severity == IssueSeverity.critical
        and issue.status in (IssueStatus.open, IssueStatus.user_review, IssueStatus.disputed)
    )
    open_high = sum(
        1
        for issue in case.issues
        if issue.severity == IssueSeverity.high
        and issue.status in (IssueStatus.open, IssueStatus.user_review, IssueStatus.disputed)
    )

    return ReadinessSummary(
        case_id=case.case_id,
        required_tasks_total=required_total,
        required_tasks_complete=required_complete,
        documents_verified=documents_verified,
        documents_total=documents_total,
        open_critical_issues=open_critical,
        open_high_issues=open_high,
        status=case.status,
        generated_at=datetime.now(timezone.utc),
    )
