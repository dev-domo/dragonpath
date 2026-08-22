import { useState } from "react";
import type { ChecklistItem } from "../types";
import "./UploadDocumentModal.css";

const ACCEPTED_EXTENSIONS =
  ".pdf,.jpg,.jpeg,.png,.bmp,.tiff,.heic,.docx,.pptx,.xlsx";

interface Props {
  candidateItems: ChecklistItem[];
  initialItemId: string;
  isUploading: boolean;
  onClose: () => void;
  onSubmit: (itemId: string, file: File) => void;
}

export function UploadDocumentModal({
  candidateItems,
  initialItemId,
  isUploading,
  onClose,
  onSubmit,
}: Props) {
  const [itemId, setItemId] = useState(initialItemId);
  const [file, setFile] = useState<File | null>(null);

  function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    if (!file) return;
    onSubmit(itemId, file);
  }

  return (
    <div className="upload-modal-scrim" onClick={isUploading ? undefined : onClose}>
      <form
        className="upload-modal"
        onClick={(event) => event.stopPropagation()}
        onSubmit={handleSubmit}
      >
        <h2 className="upload-modal__title">Upload a document</h2>
        <p className="upload-modal__description">
          Your document may contain sensitive personal information. It will be used to check
          this visa case and handled according to our privacy policy.
        </p>

        <label className="field">
          <span className="field__label">Which document is this?</span>
          <select
            className="field__input"
            value={itemId}
            onChange={(event) => setItemId(event.target.value)}
            disabled={isUploading}
          >
            {candidateItems.map((item) => (
              <option key={item.checklist_item_id} value={item.checklist_item_id}>
                {item.title_en}
              </option>
            ))}
          </select>
        </label>

        <label className="field">
          <span className="field__label">File</span>
          <input
            className="field__input upload-modal__file"
            type="file"
            accept={ACCEPTED_EXTENSIONS}
            disabled={isUploading}
            onChange={(event) => setFile(event.target.files?.[0] ?? null)}
          />
        </label>

        {isUploading && (
          <p className="upload-modal__status">
            Checking your document — this can take up to a minute…
          </p>
        )}

        <div className="upload-modal__actions">
          <button
            type="button"
            className="btn btn--secondary"
            onClick={onClose}
            disabled={isUploading}
          >
            Cancel
          </button>
          <button type="submit" className="btn btn--primary" disabled={!file || isUploading}>
            {isUploading ? "Checking…" : "Upload & check"}
          </button>
        </div>
      </form>
    </div>
  );
}
