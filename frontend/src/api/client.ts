import type { DocumentUploadResponse, OnboardingRequest, PathReviewResult, VisaCase } from "../types";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`/api${path}`, init);
  if (!response.ok) {
    const body = await response.text();
    throw new Error(`${response.status} ${response.statusText}: ${body}`);
  }
  return response.json() as Promise<T>;
}

function jsonInit(method: string, payload: unknown): RequestInit {
  return {
    method,
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  };
}

export const api = {
  reviewPath: (payload: OnboardingRequest) =>
    request<PathReviewResult>("/onboarding/path-review", jsonInit("POST", payload)),

  createCase: (payload: OnboardingRequest) =>
    request<VisaCase>("/cases", jsonInit("POST", payload)),

  getCase: (caseId: string) => request<VisaCase>(`/cases/${caseId}`),

  checkItemManually: (caseId: string, itemId: string) =>
    request<VisaCase>(`/cases/${caseId}/checklist/${itemId}/check`, { method: "POST" }),

  uncheckItemManually: (caseId: string, itemId: string) =>
    request<VisaCase>(`/cases/${caseId}/checklist/${itemId}/uncheck`, { method: "POST" }),

  uploadDocument: (caseId: string, itemId: string, file: File) => {
    const formData = new FormData();
    formData.append("file", file);
    return request<DocumentUploadResponse>(`/cases/${caseId}/checklist/${itemId}/upload`, {
      method: "POST",
      body: formData,
    });
  },
};
