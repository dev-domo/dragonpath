export type ApplicationAction = "extension" | "change";

export type CaseStatus =
  | "setup"
  | "active"
  | "at_risk"
  | "needs_attention"
  | "ready_with_confirmations"
  | "checklist_complete"
  | "archived";

export type ChecklistItemStatus =
  | "not_started"
  | "in_progress"
  | "blocked"
  | "needs_review"
  | "completed";

export type CompletionMethod =
  | "user_check"
  | "document_verified"
  | "system_resolved"
  | "official_confirmation";

export type DocumentStatus =
  | "required"
  | "uploading"
  | "parsing"
  | "needs_review"
  | "verified"
  | "failed"
  | "deleted";

export type IssueSeverity = "critical" | "high" | "medium" | "low" | "info";

export type IssueStatus = "open" | "user_review" | "disputed" | "resolved" | "dismissed";

export interface RuleSource {
  source_id: string;
  authority: string;
  title: string;
  url: string;
  last_verified_at: string;
  verification_status: "verified" | "needs_review" | "suspended" | "deprecated";
}

export interface OnboardingRequest {
  current_visa_type: string;
  application_action: ApplicationAction;
  target_visa_type?: string | null;
  stay_expiry_date: string; // YYYY-MM-DD
}

export interface PathReviewStep {
  step_number: number;
  label_en: string;
}

export interface PathReviewResult {
  supported: boolean;
  path_label_en: string;
  description_en: string;
  rule_source: RuleSource | null;
  preview_steps: PathReviewStep[];
  onboarding: OnboardingRequest;
  unsupported_reason_en: string | null;
}

export interface ChecklistItem {
  checklist_item_id: string;
  title_en: string;
  description_en: string;
  status: ChecklistItemStatus;
  completion_method: CompletionMethod;
  order: number;
  document_type: string;
  document_id: string | null;
  issue_id: string | null;
}

export interface UploadedDocument {
  document_id: string;
  original_filename: string;
  document_type: string;
  status: DocumentStatus;
  uploaded_at: string | null;
  verified_note_en: string | null;
  issue_id: string | null;
}

export interface ComparisonValue {
  source_document_id: string;
  source_label_en: string;
  value: string;
  is_mismatched: boolean;
}

export interface ValidationIssue {
  issue_id: string;
  case_id: string;
  issue_type: string;
  severity: IssueSeverity;
  title_en: string;
  explanation_en: string;
  suggested_fix_steps_en: string[];
  document_ids: string[];
  comparison_values: ComparisonValue[];
  status: IssueStatus;
  created_at: string;
}

export interface VisaCase {
  case_id: string;
  current_visa_type: string;
  application_action: ApplicationAction;
  target_visa_type: string | null;
  stay_expiry_date: string;
  status: CaseStatus;
  rule_source: RuleSource;
  checklist: ChecklistItem[];
  documents: UploadedDocument[];
  issues: ValidationIssue[];
  created_at: string;
  updated_at: string;
}

export interface DocumentUploadResponse {
  case: VisaCase;
  passed: boolean;
  issue_id: string | null;
}

export interface ReadinessSummary {
  case_id: string;
  required_tasks_total: number;
  required_tasks_complete: number;
  documents_verified: number;
  documents_total: number;
  open_critical_issues: number;
  open_high_issues: number;
  status: CaseStatus;
  generated_at: string;
}
