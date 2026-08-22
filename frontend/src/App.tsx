import { Navigate, Route, Routes } from "react-router-dom";
import { OnboardingPage } from "./pages/OnboardingPage";
import { PathReviewPage } from "./pages/PathReviewPage";
import { DashboardPage } from "./pages/DashboardPage";
import { CompletionPage } from "./pages/CompletionPage";

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Navigate to="/onboarding" replace />} />
      <Route path="/onboarding" element={<OnboardingPage />} />
      <Route path="/onboarding/review" element={<PathReviewPage />} />
      <Route path="/cases/:caseId" element={<DashboardPage />} />
      <Route path="/cases/:caseId/complete" element={<CompletionPage />} />
    </Routes>
  );
}
