import type { ValidationIssue } from "../types";
import "./MismatchDrawer.css";

interface Props {
  issue: ValidationIssue;
  onClose: () => void;
  onReplace: () => void;
}

export function MismatchDrawer({ issue, onClose, onReplace }: Props) {
  return (
    <div className="mismatch-scrim" onClick={onClose}>
      <div className="mismatch-drawer" onClick={(event) => event.stopPropagation()}>
        <div className="mismatch-drawer__header">
          <p className="mismatch-drawer__eyebrow">DOCUMENT ISSUE</p>
          <h2 className="mismatch-drawer__title">{issue.title_en}</h2>
        </div>

        {issue.comparison_values.length > 0 && (
          <div className="compared-values">
            <p className="compared-values__label">VALUES FOUND</p>
            {issue.comparison_values.map((value) => (
              <div className="compared-values__row" key={value.source_document_id}>
                <p className="compared-values__source">{value.source_label_en}</p>
                <p
                  className={`compared-values__value ${
                    value.is_mismatched ? "compared-values__value--mismatch" : ""
                  }`}
                >
                  {value.value}
                </p>
              </div>
            ))}
          </div>
        )}

        <div className="how-to-fix">
          <p className="how-to-fix__title">How to fix this</p>
          {issue.suggested_fix_steps_en.map((step, index) => (
            <p className="how-to-fix__step" key={index}>
              <span className="how-to-fix__index">{index + 1}</span>
              <span>{step}</span>
            </p>
          ))}
        </div>

        <div className="privacy-note">
          Your original file stays in this case until you replace it.
        </div>

        <div className="mismatch-drawer__spacer" />

        <button className="btn btn--primary mismatch-drawer__cta" onClick={onReplace}>
          + Upload a replacement
        </button>
      </div>
    </div>
  );
}
