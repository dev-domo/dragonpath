import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { AppHeader } from "../components/AppHeader";
import dragonMark from "../assets/character.svg";
import whiteDragon from "../assets/whiteDragon.svg";
import { api } from "../api/client";
import type { VisaCase } from "../types";
import "./CompletionPage.css";

export function CompletionPage() {
  const { caseId } = useParams<{ caseId: string }>();
  const navigate = useNavigate();
  const [visaCase, setVisaCase] = useState<VisaCase | null>(null);

  useEffect(() => {
    if (!caseId) return;
    api.getCase(caseId).then(setVisaCase);
  }, [caseId]);

  if (!visaCase) {
    return (
      <div className="app-shell">
        <AppHeader />
        <div className="dashboard-loading">Loading…</div>
      </div>
    );
  }

  const tasksComplete = visaCase.checklist.filter((item) => item.status === "completed").length;
  const filesVerified = visaCase.documents.filter((doc) => doc.status === "verified").length;
  const openIssues = visaCase.issues.filter((issue) => issue.status !== "resolved").length;

  return (
    <div className="app-shell">
      <AppHeader />
      <div className="completion-body">
        <div className="success-card">
          <div className="success-icon">
            <img className="success-icon__mark" src={dragonMark} alt="" />
            <span className="success-icon__badge">✓</span>
          </div>
          <p className="success-eyebrow">CHECKLIST COMPLETE</p>
          <h1 className="success-title">You're ready to submit</h1>
          <p className="success-description">
            Every required step is complete and your uploaded documents passed DragonPath's
            consistency checks.
          </p>

          <div className="completion-summary">
            <div className="completion-summary__item">
              <p className="completion-summary__value">
                {tasksComplete} / {visaCase.checklist.length}
              </p>
              <p className="completion-summary__label">TASKS COMPLETE</p>
            </div>
            <div className="completion-summary__item">
              <p className="completion-summary__value">{filesVerified}</p>
              <p className="completion-summary__label">FILES VERIFIED</p>
            </div>
            <div className="completion-summary__item">
              <p className="completion-summary__value">{openIssues}</p>
              <p className="completion-summary__label">OPEN ISSUES</p>
            </div>
          </div>

          <div className="submission-notice">
            <p className="submission-notice__title">One final step remains</p>
            <p className="submission-notice__detail">
              Submit through the official channel shown in your checklist. Approval is decided
              by immigration authorities.
            </p>
          </div>

          <div className="completion-actions">
            <button className="btn btn--secondary" onClick={() => navigate(`/cases/${visaCase.case_id}`)}>
              + Review checklist
            </button>
            <a
              className="btn btn--primary"
              href="https://www.moj.go.kr/immigration_eng/index.do"
              target="_blank"
              rel="noreferrer"
            >
              + Open submission guide
            </a>
          </div>
        </div>

        <img className="completion-mascot" src={whiteDragon} alt="" />
      </div>
    </div>
  );
}
