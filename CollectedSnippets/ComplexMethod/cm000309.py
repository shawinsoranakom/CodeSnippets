def format_comment(
    overlaps: list["Overlap"],
    current_pr: int,
    changes_current: dict[str, "ChangedFile"],
    all_changes: dict[int, dict[str, "ChangedFile"]]
) -> str:
    """Format the overlap report as a PR comment."""
    if not overlaps:
        return ""

    lines = ["## 🔍 PR Overlap Detection"]
    lines.append("")
    lines.append("This check compares your PR against all other open PRs targeting the same branch to detect potential merge conflicts early.")
    lines.append("")

    # Check if current PR conflicts with base branch
    format_base_conflicts(overlaps, lines)

    # Classify and sort overlaps
    classified = classify_all_overlaps(overlaps, current_pr, changes_current, all_changes)

    # Group by risk
    conflicts = [(o, r) for o, r in classified if r == 'conflict']
    medium_risk = [(o, r) for o, r in classified if r == 'medium']
    low_risk = [(o, r) for o, r in classified if r == 'low']

    # Format each section
    format_conflicts_section(conflicts, current_pr, lines)
    format_medium_risk_section(medium_risk, current_pr, changes_current, all_changes, lines)
    format_low_risk_section(low_risk, current_pr, lines)

    # Summary
    total = len(overlaps)
    lines.append(f"\n**Summary:** {len(conflicts)} conflict(s), {len(medium_risk)} medium risk, {len(low_risk)} low risk (out of {total} PRs with file overlap)")
    lines.append("\n---\n*Auto-generated on push. Ignores: `openapi.json`, lock files.*")

    return "\n".join(lines)