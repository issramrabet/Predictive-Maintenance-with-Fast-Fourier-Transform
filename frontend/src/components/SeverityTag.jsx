import { Tag } from "@carbon/react";

const SEVERITY_META = {
  ok: { color: "green", label: "Normal" },
  warn: { color: "warm-gray", label: "Surveillance" },
  danger: { color: "red", label: "Danger" },
};

// Carbon's Tag doesn't ship a semantic "warning yellow" tag color that reads
// well on g100, so warn uses a high-contrast custom tag instead of the gray default.
export default function SeverityTag({ severity, size = "md" }) {
  const meta = SEVERITY_META[severity] || SEVERITY_META.ok;
  if (severity === "warn") {
    return (
      <Tag type="high-contrast" size={size} style={{ background: "#f1c21b", color: "#161616" }}>
        {meta.label}
      </Tag>
    );
  }
  return (
    <Tag type={meta.color} size={size}>
      {meta.label}
    </Tag>
  );
}
