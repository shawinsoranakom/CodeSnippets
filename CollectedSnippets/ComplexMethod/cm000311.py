def format_low_risk_section(low_risk: list[tuple], current_pr: int, lines: list[str]):
    """Format the low risk section."""
    if not low_risk:
        return

    lines.append("### 🟢 Low Risk — File Overlap Only\n")
    lines.append("<details><summary>These PRs touch the same files but different sections (click to expand)</summary>\n")

    for o, _ in low_risk:
        other = o.pr_b if o.pr_a.number == current_pr else o.pr_a
        non_ignored = [f for f in o.overlapping_files if not should_ignore_file(f)]
        if non_ignored:
            format_pr_entry(other, lines)
            if o.line_overlaps:
                for file_path, ranges in o.line_overlaps.items():
                    range_strs = [f"L{r[0]}-{r[1]}" if r[0] != r[1] else f"L{r[0]}" for r in ranges]
                    lines.append(f"  - `{file_path}`: {', '.join(range_strs)}")
            else:
                lines.append(f"  - Shared files: `{'`, `'.join(non_ignored[:5])}`")
            lines.append("")  # Add blank line between entries

    lines.append("</details>\n")