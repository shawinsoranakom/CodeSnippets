def check_html_output(build_dir: Path) -> str:
    """Check built HTML for broken formatting and empty pages."""
    issues = []

    if not build_dir.exists():
        return "ERROR: build/html directory not found. Run 'make html' first.\n"

    for html_file in sorted(build_dir.rglob("*.html")):
        rel = html_file.relative_to(build_dir)
        if rel.name in ("search.html", "genindex.html", "objects.inv"):
            continue

        try:
            content = html_file.read_text(errors="replace")
        except Exception as e:
            issues.append((str(rel), f"cannot read: {e}"))
            continue

        for pattern, description in BROKEN_PATTERNS:
            matches = pattern.findall(content)
            if matches:
                issues.append((str(rel), f"{description} ({len(matches)}x)"))

        if str(rel).startswith("api/"):
            text = re.sub(r"<[^>]+>", "", content)
            text = re.sub(r"\s+", " ", text).strip()
            if len(text) < MIN_CONTENT_LENGTH:
                issues.append((str(rel), f"possibly empty page ({len(text)} chars)"))

    lines = []
    lines.append("HTML Formatting Check")
    lines.append("=" * 50)
    lines.append("")

    if not issues:
        lines.append("No issues found.")
    else:
        lines.append(f"Found {len(issues)} issue(s):")
        lines.append("")
        lines.append(f"{'File':<55} Issue")
        lines.append("-" * 90)
        for filepath, issue in issues:
            lines.append(f"{filepath:<55} {issue}")

    lines.append("")
    return "\n".join(lines)