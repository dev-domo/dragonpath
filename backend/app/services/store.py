"""In-memory persistence for the MVP scaffold.

There is no database wired up yet. Every process restart resets state.
The store's method signatures mirror the shapes FS-04 through FS-16
describe, so swapping this for a real database layer later should not
require changing the API routes.
"""

from __future__ import annotations

import re
import uuid
from datetime import datetime, timezone
from typing import Optional

from app.data.seed import DEMO_D2_2_EXTENSION_SOURCE
from app.models.schemas import (
    CaseStatus,
    ChecklistItem,
    ChecklistItemStatus,
    CompletionMethod,
    DocumentStatus,
    IssueSeverity,
    IssueStatus,
    OnboardingRequest,
    UploadedDocument,
    ValidationIssue,
    VisaCase,
)
from app.services.upstage_document_agent import DocumentCheckResult

DEFAULT_FIX_TEXT = (
    "DragonPath could not confirm this document meets the requirement. "
    "Double-check it is the right document and that no required fields "
    "are blank, then upload it again."
)


def _new_id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:8]}"


_LIST_MARKER_RE = re.compile(r"^(?:[-*•]|\d+[.)])\s+")


def _split_fix_steps(fix_text: str) -> list[str]:
    """Turn the agent's raw "how to fix" text into a list of discrete
    steps, so the UI can number them (1, 2, 3, ...) instead of dumping
    one undifferentiated paragraph. Splits on newlines and strips any
    list markers/numbering the source text already has, since the UI
    supplies its own numbering.
    """
    lines = [line.strip() for line in fix_text.splitlines()]
    lines = [line for line in lines if line]
    if not lines:
        cleaned = fix_text.strip()
        return [cleaned] if cleaned else []
    return [_LIST_MARKER_RE.sub("", line).strip() for line in lines]


class InvalidTransitionError(Exception):
    pass


class CaseStore:
    def __init__(self) -> None:
        self._cases: dict[str, VisaCase] = {}

    def create_case(self, onboarding: OnboardingRequest) -> VisaCase:
        """Seed the checklist with the required-document list for this
        visa path. Per product direction, nothing starts pre-verified —
        every item begins `not_started` (rendered gray) until the user
        uploads the matching document, or manually checks it off.
        """
        now = datetime.now(timezone.utc)
        case_id = _new_id("case")

        checklist = [
            ChecklistItem(
                checklist_item_id=_new_id("item"),
                title_en="Passport Bio Page",
                description_en="Upload your passport bio page to confirm your identity.",
                status=ChecklistItemStatus.not_started,
                completion_method=CompletionMethod.document_verified,
                order=1,
                document_type="personal_details",
            ),
            ChecklistItem(
                checklist_item_id=_new_id("item"),
                title_en="Certificate of Enrollment",
                description_en="Certificate of enrollment issued by your school.",
                status=ChecklistItemStatus.not_started,
                completion_method=CompletionMethod.document_verified,
                order=2,
                document_type="proof_of_enrollment",
            ),
            ChecklistItem(
                checklist_item_id=_new_id("item"),
                title_en="Application Form for Extension of Sojourn Period",
                description_en="The visa extension application form for this case.",
                status=ChecklistItemStatus.not_started,
                completion_method=CompletionMethod.document_verified,
                order=3,
                document_type="application_form",
            ),
            ChecklistItem(
                checklist_item_id=_new_id("item"),
                title_en="Bank Balance Certificate",
                description_en="A recent bank balance certificate.",
                status=ChecklistItemStatus.not_started,
                completion_method=CompletionMethod.document_verified,
                order=4,
                document_type="financial_proof",
            ),
        ]

        case = VisaCase(
            case_id=case_id,
            current_visa_type=onboarding.current_visa_type,
            application_action=onboarding.application_action,
            target_visa_type=onboarding.target_visa_type,
            stay_expiry_date=onboarding.stay_expiry_date,
            status=CaseStatus.active,
            rule_source=DEMO_D2_2_EXTENSION_SOURCE,
            checklist=checklist,
            documents=[],
            issues=[],
            created_at=now,
            updated_at=now,
        )
        self._cases[case_id] = case
        return case

    def get_case(self, case_id: str) -> Optional[VisaCase]:
        return self._cases.get(case_id)

    def mark_item_checked_manually(self, case_id: str, item_id: str) -> VisaCase:
        """The manual gray -> blue toggle: a user can hand-confirm a
        pending item without uploading anything. It also doubles as the
        manual override for a needs_review (red) item — e.g. when the
        checklist item was only flagged because documents were approved
        out of order rather than an actual document problem — clicking
        the checkbox again resolves it straight to blue. It cannot undo
        an already-completed item — that is what uncheck_item_manually
        is for.
        """
        case = self._require_case(case_id)
        item = self._require_item(case, item_id)
        if item.status not in (
            ChecklistItemStatus.not_started,
            ChecklistItemStatus.needs_review,
        ):
            raise InvalidTransitionError(
                "Only a pending or flagged item can be checked off manually."
            )

        now = datetime.now(timezone.utc)

        if item.status == ChecklistItemStatus.needs_review:
            for existing in case.issues:
                if existing.issue_id == item.issue_id:
                    existing.status = IssueStatus.resolved
            document = next(
                (doc for doc in case.documents if doc.document_id == item.document_id), None
            )
            if document is not None:
                document.status = DocumentStatus.verified
                document.verified_note_en = "Verified"
                document.issue_id = None
            item.issue_id = None

        item.status = ChecklistItemStatus.completed
        item.completion_method = CompletionMethod.user_check
        case.updated_at = now
        self._recompute_case_status(case)
        return case

    def uncheck_item_manually(self, case_id: str, item_id: str) -> VisaCase:
        """Undo a hand-confirmed check: blue -> gray.

        This only reverses a check the user made by hand. An item that a
        real uploaded document completed still has that document attached,
        and un-checking it would leave the checklist contradicting the
        agent's verdict, so that stays locked — replace the document
        instead.
        """
        case = self._require_case(case_id)
        item = self._require_item(case, item_id)
        if item.status != ChecklistItemStatus.completed:
            raise InvalidTransitionError("Only a completed item can be un-checked.")
        if item.document_id is not None:
            raise InvalidTransitionError(
                "This item was completed by a checked document. Upload a "
                "replacement instead of un-checking it."
            )

        item.status = ChecklistItemStatus.not_started
        item.completion_method = CompletionMethod.document_verified
        case.updated_at = datetime.now(timezone.utc)
        self._recompute_case_status(case)
        return case

    def apply_document_check(
        self,
        case_id: str,
        item_id: str,
        original_filename: str,
        result: DocumentCheckResult,
    ) -> tuple[VisaCase, ChecklistItem, Optional[ValidationIssue]]:
        case = self._require_case(case_id)
        item = self._require_item(case, item_id)
        if item.status == ChecklistItemStatus.completed:
            raise InvalidTransitionError("This document has already been verified.")

        now = datetime.now(timezone.utc)

        document = next(
            (doc for doc in case.documents if doc.document_id == item.document_id), None
        )
        if document is None:
            document = UploadedDocument(
                document_id=_new_id("doc"),
                original_filename=original_filename,
                document_type=item.document_type,
                status=DocumentStatus.verified,
                uploaded_at=now,
            )
            case.documents.append(document)
            item.document_id = document.document_id
        else:
            document.original_filename = original_filename
            document.uploaded_at = now

        issue: Optional[ValidationIssue] = None

        if result.passed:
            document.status = DocumentStatus.verified
            document.verified_note_en = "Verified"
            document.issue_id = None
            item.status = ChecklistItemStatus.completed
            for existing in case.issues:
                if existing.issue_id == item.issue_id:
                    existing.status = IssueStatus.resolved
            item.issue_id = None
        else:
            fix_text = result.how_to_fix or DEFAULT_FIX_TEXT
            document.status = DocumentStatus.needs_review
            document.verified_note_en = "Needs attention"

            existing_issue = next(
                (i for i in case.issues if i.issue_id == item.issue_id), None
            )
            if existing_issue is not None:
                existing_issue.explanation_en = fix_text
                existing_issue.suggested_fix_steps_en = [fix_text]
                existing_issue.status = IssueStatus.open
                existing_issue.document_ids = [document.document_id]
                issue = existing_issue
            else:
                issue = ValidationIssue(
                    issue_id=_new_id("issue"),
                    case_id=case.case_id,
                    issue_type="document_check_failed",
                    severity=IssueSeverity.high,
                    title_en=f"Fix an issue with {item.title_en.lower()}",
                    explanation_en=fix_text,
                    suggested_fix_steps_en=[fix_text],
                    document_ids=[document.document_id],
                    status=IssueStatus.open,
                    created_at=now,
                )
                case.issues.append(issue)

            document.issue_id = issue.issue_id
            item.issue_id = issue.issue_id
            item.status = ChecklistItemStatus.needs_review

        case.updated_at = now
        self._recompute_case_status(case)
        return case, item, issue

    def _require_case(self, case_id: str) -> VisaCase:
        case = self._cases.get(case_id)
        if case is None:
            raise KeyError(case_id)
        return case

    def _require_item(self, case: VisaCase, item_id: str) -> ChecklistItem:
        item = next((i for i in case.checklist if i.checklist_item_id == item_id), None)
        if item is None:
            raise KeyError(item_id)
        return item

    def _recompute_case_status(self, case: VisaCase) -> None:
        statuses = [item.status for item in case.checklist]
        if any(status == ChecklistItemStatus.needs_review for status in statuses):
            case.status = CaseStatus.needs_attention
        elif any(status == ChecklistItemStatus.not_started for status in statuses):
            case.status = CaseStatus.active
        else:
            case.status = CaseStatus.checklist_complete


store = CaseStore()
