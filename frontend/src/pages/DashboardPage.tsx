import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { AppHeader } from "../components/AppHeader";
import { MismatchDrawer } from "../components/MismatchDrawer";
import { DocumentCheckbox } from "../components/DocumentCheckbox";
import { UploadDocumentModal } from "../components/UploadDocumentModal";
import { api } from "../api/client";
import type { ChecklistItem, ValidationIssue, VisaCase } from "../types";
import "./DashboardPage.css";

function toneForStatus(status: ChecklistItem["status"]): "gray" | "blue" | "red" {
  if (status === "completed") return "blue";
  if (status === "needs_review") return "red";
  return "gray";
}

export function DashboardPage() {
  const { caseId } = useParams<{ caseId: string }>();
  const navigate = useNavigate();
  const [visaCase, setVisaCase] = useState<VisaCase | null>(null);
  const [activeIssue, setActiveIssue] = useState<ValidationIssue | null>(null);
  const [uploadTargetItemId, setUploadTargetItemId] = useState<string | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);

  useEffect(() => {
    if (!caseId) return;
    api.getCase(caseId).then(setVisaCase);
  }, [caseId]);

  if (!visaCase) {
    return (
      <div className="app-shell">
        <AppHeader />
        <div className="dashboard-loading">Loading your case…</div>
      </div>
    );
  }

  const completedCount = visaCase.checklist.filter((item) => item.status === "completed").length;
  const isChecklistComplete = visaCase.status === "checklist_complete";
  const daysRemaining = Math.max(
    0,
    Math.ceil(
      (new Date(visaCase.stay_expiry_date).getTime() - Date.now()) / (1000 * 60 * 60 * 24)
    )
  );

  function findIssue(issueId: string | null) {
    if (!issueId) return null;
    return visaCase!.issues.find((issue) => issue.issue_id === issueId) ?? null;
  }

  async function handleRowClick(item: ChecklistItem) {
    if (item.status === "not_started") {
      const updated = await api.checkItemManually(visaCase!.case_id, item.checklist_item_id);
      setVisaCase(updated);
      return;
    }
    if (item.status === "needs_review") {
      setActiveIssue(findIssue(item.issue_id));
    }
  }

  async function handleCheckboxClick(event: React.MouseEvent, item: ChecklistItem) {
    event.stopPropagation();
    if (item.status !== "not_started" && item.status !== "needs_review") return;
    const updated = await api.checkItemManually(visaCase!.case_id, item.checklist_item_id);
    setVisaCase(updated);
  }

  function openUploadModal(itemId: string) {
    setActiveIssue(null);
    setUploadError(null);
    setUploadTargetItemId(itemId);
  }

  async function handleUploadSubmit(itemId: string, file: File) {
    setIsUploading(true);
    setUploadError(null);
    try {
      const response = await api.uploadDocument(visaCase!.case_id, itemId, file);
      setVisaCase(response.case);
      setUploadTargetItemId(null);
      if (!response.passed && response.issue_id) {
        const issue = response.case.issues.find((i) => i.issue_id === response.issue_id);
        if (issue) setActiveIssue(issue);
      }
    } catch (err) {
      setUploadError(err instanceof Error ? err.message : "Upload failed. Please try again.");
    } finally {
      setIsUploading(false);
    }
  }

  const uploadCandidates = visaCase.checklist.filter((item) => item.status !== "completed");
  const needsAttentionCount = visaCase.documents.filter((doc) => doc.status === "needs_review")
    .length;

  return (
    <div className="app-shell">
      <AppHeader />
      <div className="dashboard-body">
        <nav className="dashboard-nav">
          <div>
            <p className="dashboard-nav__eyebrow">MY VISA CASE</p>
            <div className="dashboard-nav__current-case">
              <p className="dashboard-nav__case-label">
                {visaCase.current_visa_type}{" "}
                {visaCase.application_action === "extension" ? "Extension" : "Change"}
              </p>
              <p className="dashboard-nav__case-deadline">Deadline · {daysRemaining} days</p>
            </div>
          </div>
          <div className="dashboard-nav__help">
            <p className="dashboard-nav__help-title">Need help?</p>
            <p className="dashboard-nav__help-detail">
              Review official source links or contact your university office.
            </p>
          </div>
        </nav>

        <main className="checklist-workspace">
          <div className="workspace-heading">
            <div>
              <h1 className="workspace-heading__title">
                Your {visaCase.current_visa_type}{" "}
                {visaCase.application_action === "extension" ? "extension" : "change"}
              </h1>
              <p className="workspace-heading__subtitle">
                Complete each step in order. DragonPath will keep checking your files.
              </p>
            </div>
            <span className="progress-badge">
              {completedCount} of {visaCase.checklist.length} done
            </span>
          </div>

          <div className="deadline-guidance">
            <div>
              <p className="deadline-guidance__title">Recommended: submit within 14 days</p>
              <p className="deadline-guidance__detail">
                Your current stay expires on{" "}
                {new Date(visaCase.stay_expiry_date).toLocaleDateString("en-GB", {
                  day: "numeric",
                  month: "long",
                })}
                . Leave time for corrections.
              </p>
            </div>
          </div>

          <section className="checklist-section">
            <div className="checklist-section__header">
              <h2>Next steps</h2>
              <div className="checklist-section__rule" />
              <span>IN RECOMMENDED ORDER</span>
            </div>

            {visaCase.checklist.map((item) => (
              <button
                key={item.checklist_item_id}
                className="checklist-row"
                onClick={() => handleRowClick(item)}
              >
                <DocumentCheckbox
                  tone={toneForStatus(item.status)}
                  onClick={(event) => handleCheckboxClick(event, item)}
                />
                <div className="checklist-row__body">
                  <p className="checklist-row__title">{item.title_en}</p>
                  <p className="checklist-row__description">{item.description_en}</p>
                </div>
                {item.status === "completed" && <span className="status-chip status-chip--completed">done</span>}
                {item.status === "needs_review" && (
                  <span className="status-chip status-chip--needs_review">Needs attention</span>
                )}
              </button>
            ))}
          </section>

          <div className="complete-bar">
            <button
              className={`complete-button ${isChecklistComplete ? "complete-button--enabled" : ""}`}
              disabled={!isChecklistComplete}
              onClick={() => navigate(`/cases/${visaCase.case_id}/complete`)}
            >
              Complete
            </button>
          </div>
        </main>

        <aside className="documents-panel">
          <div>
            <h2 className="documents-panel__title">Your documents</h2>
            <p className="documents-panel__caption">
              {visaCase.documents.length} files uploaded · {needsAttentionCount} needs attention
            </p>
          </div>

          <button
            className="btn btn--primary documents-panel__upload"
            disabled={uploadCandidates.length === 0}
            onClick={() => {
              if (uploadCandidates[0]) openUploadModal(uploadCandidates[0].checklist_item_id);
            }}
          >
            + Upload document
          </button>

          <div className="documents-list">
            {visaCase.documents.map((doc) => (
              <div className="document-row" key={doc.document_id}>
                <div className="document-row__main">
                  <span
                    className={`document-row__badge ${
                      doc.status === "needs_review" ? "document-row__badge--error" : ""
                    }`}
                  />
                  <div>
                    <p className="document-row__filename">{doc.original_filename}</p>
                    <p className="document-row__meta">{doc.verified_note_en}</p>
                  </div>
                </div>
                {doc.status === "needs_review" && doc.issue_id && (
                  <button
                    className="document-row__issue"
                    onClick={() => setActiveIssue(findIssue(doc.issue_id))}
                  >
                    Needs attention — view details
                  </button>
                )}
              </div>
            ))}
            {visaCase.documents.length === 0 && (
              <p className="documents-list__empty">No documents uploaded yet.</p>
            )}
          </div>

          <div className="documents-panel__spacer" />

          <div className="source-status">
            <p className="source-status__title">SOURCE STATUS</p>
            <p className="source-status__detail">
              Guidance checked against the latest official source.
            </p>
          </div>
        </aside>
      </div>

      {activeIssue && (
        <MismatchDrawer
          issue={activeIssue}
          onClose={() => setActiveIssue(null)}
          onReplace={() => {
            const item = visaCase.checklist.find((i) => i.issue_id === activeIssue.issue_id);
            if (item) openUploadModal(item.checklist_item_id);
          }}
        />
      )}

      {uploadTargetItemId && (
        <UploadDocumentModal
          candidateItems={uploadCandidates}
          initialItemId={uploadTargetItemId}
          isUploading={isUploading}
          onClose={() => setUploadTargetItemId(null)}
          onSubmit={handleUploadSubmit}
        />
      )}
      {uploadError && (
        <div className="upload-toast" onClick={() => setUploadError(null)}>
          {uploadError}
        </div>
      )}
    </div>
  );
}
