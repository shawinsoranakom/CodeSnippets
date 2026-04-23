def format_line_overlaps(line_overlaps: dict[str, list[tuple]], lines: list[str]):
    """Format line overlap details."""
    all_paths = list(line_overlaps.keys())
    common_prefix = find_common_prefix(all_paths) if len(all_paths) > 1 else ""
    if common_prefix:
        lines.append(f"  - 📁 `{common_prefix}`")
    for file_path, ranges in line_overlaps.items():
        display_path = file_path[len(common_prefix):] if common_prefix else file_path
        range_strs = [f"L{r[0]}-{r[1]}" if r[0] != r[1] else f"L{r[0]}" for r in ranges]
        indent = "    " if common_prefix else "  "
        lines.append(f"{indent}- `{display_path}`: {', '.join(range_strs)}")