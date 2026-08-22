import { useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { AppHeader } from "../components/AppHeader";
import { api } from "../api/client";
import type { PathReviewResult } from "../types";
import "./PathReviewPage.css";

export function PathReviewPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const review = (location.state as { review?: PathReviewResult } | null)?.review;
  const [isCreating, setIsCreating] = useState(false);

  if (!review) {
    navigate("/onboarding", { replace: true });
    return null;
  }

  async function handleCreateChecklist() {
    setIsCreating(true);
    try {
      const visaCase = await api.createCase(review!.onboarding);
      navigate(`/cases/${visaCase.case_id}`);
    } finally {
      setIsCreating(false);
    }
  }

  return (
    <div className="app-shell">
      <AppHeader />
      <div className="path-review-body">
        <div className="path-review-card">
          {review.supported ? (
            <>
              <span className="supported-badge">SUPPORTED PATH</span>
              <h1 className="path-title">{review.path_label_en}</h1>
              <p className="path-description">{review.description_en}</p>

              <div className="case-details">
                <div className="case-details__item">
                  <p className="case-details__label">CURRENT STAY EXPIRY</p>
                  <p className="case-details__value">{review.onboarding.stay_expiry_date}</p>
                </div>
                {review.rule_source && (
                  <div className="case-details__item">
                    <p className="case-details__label">RULE STATUS</p>
                    <p className="case-details__value case-details__value--link">
                      Sources verified{" "}
                      {new Date(review.rule_source.last_verified_at).toLocaleDateString("en-GB", {
                        day: "numeric",
                        month: "short",
                        year: "numeric",
                      })}
                    </p>
                  </div>
                )}
              </div>

              <div className="divider" />

              <h2 className="preview-heading">Your checklist will start with</h2>
              <div className="checklist-preview">
                {review.preview_steps.map((step) => (
                  <div className="checklist-preview__item" key={step.step_number}>
                    <span className="checklist-preview__number">{step.step_number}</span>
                    <span className="checklist-preview__label">{step.label_en}</span>
                  </div>
                ))}
              </div>

              <div className="path-review-actions">
                <button className="btn btn--secondary" onClick={() => navigate("/onboarding")}>
                  Edit answers
                </button>
                <button
                  className="btn btn--primary"
                  onClick={handleCreateChecklist}
                  disabled={isCreating}
                >
                  {isCreating ? "Creating…" : "Create my checklist"}
                </button>
              </div>
            </>
          ) : (
            <>
              <span className="supported-badge supported-badge--unsupported">
                NOT YET SUPPORTED
              </span>
              <h1 className="path-title">{review.path_label_en}</h1>
              <p className="path-description">{review.unsupported_reason_en}</p>
              <div className="path-review-actions">
                <button className="btn btn--secondary" onClick={() => navigate("/onboarding")}>
                  Edit answers
                </button>
                <a
                  className="btn btn--primary"
                  href="https://www.moj.go.kr/immigration_eng/1862/subview.do"
                  target="_blank"
                  rel="noreferrer"
                >
                  View official sources
                </a>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
