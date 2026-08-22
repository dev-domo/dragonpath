import "./DocumentCheckbox.css";

type Tone = "gray" | "blue" | "red";

interface Props {
  tone: Tone;
}

export function DocumentCheckbox({ tone }: Props) {
  return (
    <span className={`doc-checkbox doc-checkbox--${tone}`} aria-hidden>
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
    </span>
  );
}
