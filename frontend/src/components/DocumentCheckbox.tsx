import "./DocumentCheckbox.css";

type Tone = "gray" | "blue" | "red";

interface Props {
  tone: Tone;
  /** Completed by a checked document, so the user cannot toggle it off. */
  locked?: boolean;
  onClick?: (event: React.MouseEvent) => void;
}

const CHECK_ICON = (
  <svg viewBox="0 0 16 16" width="18" height="18">
    <path
      d="M3 8.5L6.2 11.5L13 4.5"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
  </svg>
);

export function DocumentCheckbox({ tone, locked = false, onClick }: Props) {
  if (onClick) {
    return (
      <button
        type="button"
        className={`doc-checkbox doc-checkbox--${tone} doc-checkbox--clickable${
          locked ? " doc-checkbox--locked" : ""
        }`}
        aria-pressed={tone === "blue"}
        onClick={onClick}
      >
        {CHECK_ICON}
      </button>
    );
  }

  return (
    <span className={`doc-checkbox doc-checkbox--${tone}`} aria-hidden>
      {CHECK_ICON}
    </span>
  );
}
