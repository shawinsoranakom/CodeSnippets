def _remove_repeated_page_elements(markdown: str) -> str:
    """
    Remove repeated page footer/header patterns from markdown.

    Detects short text patterns that appear many times (5+) in the document,
    which are likely page headers or footers that got repeated during conversion.

    Examples of patterns this catches:
    - "- 32 2025 Annual Meeting of Stockholders"
    - "Company Name | Page 5"
    - "CONFIDENTIAL"
    """
    lines = markdown.split("\n")

    # Find candidate repeated lines (short lines that appear multiple times)
    # Normalize lines by stripping and replacing page numbers with placeholder
    def normalize_line(line: str) -> str:
        """Normalize a line for comparison by replacing variable parts."""
        normalized = line.strip()
        # Replace page numbers (standalone digits) with placeholder
        normalized = re.sub(r"\b\d{1,3}\b", "#", normalized)
        # Replace markdown image URLs with placeholder, but keep the image marker
        # so we can distinguish "text with image" from "standalone image"
        normalized = re.sub(r"!\[([^\]]*)\]\([^)]+\)", r"![IMG]", normalized)
        # Also replace HTML <img> tags with placeholder
        normalized = re.sub(r"<img[^>]+>", "[IMG]", normalized)
        return normalized

    # Count normalized patterns
    line_counts: Counter = Counter()

    for line in lines:
        stripped = line.strip()
        normalized = normalize_line(stripped)
        # Only consider lines that normalize to short patterns (< 80 chars after normalization)
        # that aren't empty, headers, table rows, or STANDALONE images
        # Standalone images like ![LOGO](url) or <img ...> should NOT be removed
        if (
            normalized
            and len(normalized) < 80
            and not stripped.startswith("#")  # Not a header
            and not stripped.startswith("|")  # Not a table row
            and not stripped.startswith("[")  # Not a link
            and not re.match(r"^!\[", stripped)  # Not a standalone markdown image
            and not re.match(r"^<img\s", stripped)  # Not a standalone HTML image
            and not re.match(r"^<div[\s>]", stripped)  # Not an HTML div block
            and stripped != "---"
        ):  # Not a horizontal rule
            line_counts[normalized] += 1

    # Find patterns that repeat 5+ times (likely page footers/headers)
    repeated_patterns = {
        pattern for pattern, count in line_counts.items() if count >= 5
    }

    if not repeated_patterns:
        return markdown

    # Filter out the repeated lines
    filtered_lines = []
    for line in lines:
        stripped = line.strip()
        normalized = normalize_line(stripped)
        if normalized in repeated_patterns:
            # Skip this repeated page element
            continue
        filtered_lines.append(line)

    return "\n".join(filtered_lines)