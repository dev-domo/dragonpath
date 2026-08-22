"""Pydantic models for the DragonPath MVP.

These mirror the data objects defined in D-08 Functional Specification
(section 6), trimmed to what the MVP screens in the Figma file actually
need. Field names intentionally match the spec so this can be extended
without renaming later.
"""

from __future__ import annotations

from datetime import date, datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class ApplicationAction(str, Enum):
    extension = "extension"
    change = "change"


class CaseStatus(str, Enum):
    setup = "setup"
    active = "active"
    at_risk = "at_risk"
    needs_attention = "needs_attention"
    ready_with_confirmations = "ready_with_confirmations"
    checklist_complete = "checklist_complete"
    archived = "archived"


class ChecklistItemStatus(str, Enum):
    not_started = "not_started"
    in_progress = "in_progress"
    blocked = "blocked"
    needs_review = "needs_review"
    completed = "completed"


class CompletionMethod(str, Enum):
    user_check = "user_check"
    document_verified = "document_verified"
    system_resolved = "system_resolved"
    official_confirmation = "official_confirmation"


class DocumentStatus(str, Enum):
    required = "required"
    uploading = "uploading"
    parsing = "parsing"
    needs_review = "needs_review"
    verified = "verified"
    failed = "failed"
    deleted = "deleted"


class IssueSeverity(str, Enum):
    critical = "critical"
    high = "high"
    medium = "medium"
    low = "low"
    info = "info"


class IssueStatus(str, Enum):
    open = "open"
    user_review = "user_review"
    disputed = "disputed"
    resolved = "resolved"
    dismissed = "dismissed"


class RuleVerificationStatus(str, Enum):
    verified = "verified"
    needs_review = "needs_review"
    suspended = "suspended"
    deprecated = "deprecated"


# --- Rule sourcing (D-06 Principle 1 / D-08 FS-02, FS-17) ---------------


class RuleSource(BaseModel):
    source_id: str
    authority: str
    title: str
    url: str
    last_verified_at: datetime
    verification_status: RuleVerificationStatus


# --- Onboarding ----------------------------------------------------------


class OnboardingRequest(BaseModel):
    current_visa_type: str = Field(..., examples=["D-2-2"])
    application_action: ApplicationAction
    target_visa_type: Optional[str] = None
    stay_expiry_date: date


class PathReviewStep(BaseModel):
    step_number: int
    label_en: str


class PathReviewResult(BaseModel):
    supported: bool
    path_label_en: str
    description_en: str
    rule_source: Optional[RuleSource] = None
    preview_steps: list[PathReviewStep] = Field(default_factory=list)
    onboarding: OnboardingRequest
    unsupported_reason_en: Optional[str] = None


# --- Checklist -------------------------------------------------------------


class ChecklistItem(BaseModel):
    checklist_item_id: str
    title_en: str
    description_en: str
    status: ChecklistItemStatus
    completion_method: CompletionMethod
    order: int
    document_type: str
    document_id: Optional[str] = None
    issue_id: Optional[str] = None


# --- Documents ---------------------------------------------------------------


class UploadedDocument(BaseModel):
    document_id: str
    original_filename: str
    document_type: str
    status: DocumentStatus
    uploaded_at: Optional[datetime] = None
    verified_note_en: Optional[str] = None
    issue_id: Optional[str] = None


# --- Validation issues -------------------------------------------------------


class ComparisonValue(BaseModel):
    source_document_id: str
    source_label_en: str
    value: str
    is_mismatched: bool = False


class ValidationIssue(BaseModel):
    issue_id: str
    case_id: str
    issue_type: str
    severity: IssueSeverity
    title_en: str
    explanation_en: str
    suggested_fix_steps_en: list[str]
    document_ids: list[str]
    comparison_values: list[ComparisonValue] = Field(default_factory=list)
    status: IssueStatus
    created_at: datetime


# --- Visa case ----------------------------------------------------------------


class VisaCase(BaseModel):
    case_id: str
    current_visa_type: str
    application_action: ApplicationAction
    target_visa_type: Optional[str]
    stay_expiry_date: date
    status: CaseStatus
    rule_source: RuleSource
    checklist: list[ChecklistItem]
    documents: list[UploadedDocument]
    issues: list[ValidationIssue]
    created_at: datetime
    updated_at: datetime


class ReadinessSummary(BaseModel):
    case_id: str
    required_tasks_total: int
    required_tasks_complete: int
    documents_verified: int
    documents_total: int
    open_critical_issues: int
    open_high_issues: int
    status: CaseStatus
    generated_at: datetime
