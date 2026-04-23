def _normalize_text(text: str) -> str:
    """Normalize text while preserving Markdown structures like tables, admonitions, and code blocks."""
    if not text:
        return ""
    # Check if text contains Markdown structures that need line preservation
    if any(marker in text for marker in ("|", "!!!", "```", "\n#", "\n- ", "\n* ", "\n1. ", "\n    ")):
        # Preserve Markdown formatting - just strip trailing whitespace from lines
        return "\n".join(line.rstrip() for line in text.splitlines()).strip()
    # Simple text - collapse single newlines within paragraphs
    paragraphs: list[str] = []
    current: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            if current:
                paragraphs.append(" ".join(current))
                current = []
            continue
        current.append(stripped)
    if current:
        paragraphs.append(" ".join(current))
    return "\n\n".join(paragraphs)