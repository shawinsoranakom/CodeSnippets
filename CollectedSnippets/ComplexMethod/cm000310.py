def format_medium_risk_section(
    medium_risk: list[tuple],
    current_pr: int,
    changes_current: dict,
    all_changes: dict,
    lines: list[str]
):
    """Format the medium risk section."""
    if not medium_risk:
        return

    lines.append("### 🟡 Medium Risk — Some Line Overlap\n")
    lines.append("These PRs have some overlapping changes:\n")

    for o, _ in medium_risk:
        other = o.pr_b if o.pr_a.number == current_pr else o.pr_a
        other_changes = all_changes.get(other.number, {})
        format_pr_entry(other, lines)

        # Note if rename is involved
        for file_path in o.overlapping_files:
            file_a = changes_current.get(file_path)
            file_b = other_changes.get(file_path)
            if (file_a and file_a.is_rename) or (file_b and file_b.is_rename):
                lines.append(f"  - ⚠️ `{file_path}` is being renamed/moved")
                break

        if o.line_overlaps:
            for file_path, ranges in o.line_overlaps.items():
                range_strs = [f"L{r[0]}-{r[1]}" if r[0] != r[1] else f"L{r[0]}" for r in ranges]
                lines.append(f"  - `{file_path}`: {', '.join(range_strs)}")
        else:
            non_ignored = [f for f in o.overlapping_files if not should_ignore_file(f)]
            if non_ignored:
                lines.append(f"  - Shared files: `{'`, `'.join(non_ignored[:5])}`")
        lines.append("")