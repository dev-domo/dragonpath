import { FormEvent, useState } from "react";
import { useNavigate } from "react-router-dom";
import { AppHeader } from "../components/AppHeader";
import { api } from "../api/client";
import type { ApplicationAction } from "../types";
import "./OnboardingPage.css";

const CURRENT_VISA_OPTIONS = [{ value: "D-2-2", label: "D-2-2 — Bachelor's degree student" }];

export function OnboardingPage() {
  const navigate = useNavigate();
  const [action, setAction] = useState<ApplicationAction>("extension");
  const [currentVisaType, setCurrentVisaType] = useState(CURRENT_VISA_OPTIONS[0].value);
  const [stayExpiryDate, setStayExpiryDate] = useState("2026-10-31");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setIsSubmitting(true);
    setError(null);
    try {
      const onboarding = {
        current_visa_type: currentVisaType,
        application_action: action,
        stay_expiry_date: stayExpiryDate,
      };
      const review = await api.reviewPath(onboarding);
      navigate("/onboarding/review", { state: { review } });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong. Please try again.");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div className="app-shell">
      <AppHeader />
      <div className="onboarding-body">
        <aside className="onboarding-aside">
          <p className="onboarding-aside__step">STEP 1 OF 3</p>
          <h1 className="onboarding-aside__title">
            Tell us about
            <br />
            your visa path
          </h1>
          <p className="onboarding-aside__description">
            We only ask for details that change your checklist and deadlines.
          </p>
          <div className="onboarding-aside__track">
            <div className="onboarding-aside__fill" style={{ width: "33%" }} />
          </div>
        </aside>

        <div className="onboarding-form-region">
          <form className="onboarding-card" onSubmit={handleSubmit}>
            <h2 className="onboarding-card__title">What would you like to do?</h2>
            <p className="onboarding-card__subtitle">
              We'll build a checklist for one visa case at a time.
            </p>

            <div className="visa-action-options">
              <button
                type="button"
                className={`visa-action-option ${action === "extension" ? "is-selected" : ""}`}
                onClick={() => setAction("extension")}
              >
                <div className="visa-action-option__heading">
                  <span className={`radio-dot ${action === "extension" ? "is-selected" : ""}`} />
                  <span className="visa-action-option__title">Extend my current visa</span>
                </div>
                <p className="visa-action-option__description">
                  Stay in the same visa category for a longer period.
                </p>
              </button>

              <button
                type="button"
                className={`visa-action-option ${action === "change" ? "is-selected" : ""}`}
                onClick={() => setAction("change")}
              >
                <div className="visa-action-option__heading">
                  <span className={`radio-dot ${action === "change" ? "is-selected" : ""}`} />
                  <span className="visa-action-option__title">Change to another visa</span>
                </div>
                <p className="visa-action-option__description">
                  Move from your current visa to a different status.
                </p>
              </button>
            </div>

            <label className="field">
              <span className="field__label">Current visa type</span>
              <select
                className="field__input"
                value={currentVisaType}
                onChange={(event) => setCurrentVisaType(event.target.value)}
              >
                {CURRENT_VISA_OPTIONS.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </label>

            <label className="field">
              <span className="field__label">Current stay expiry date</span>
              <input
                className="field__input"
                type="date"
                value={stayExpiryDate}
                onChange={(event) => setStayExpiryDate(event.target.value)}
              />
            </label>

            {error && <p className="onboarding-error">{error}</p>}

            <div className="onboarding-actions">
              <button className="btn btn--primary" type="submit" disabled={isSubmitting}>
                {isSubmitting ? "Checking…" : "Continue"}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}
