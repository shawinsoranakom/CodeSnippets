def format_conflict_details(overlap: "Overlap", lines: list[str]):
    """Format conflict details for a PR."""
    if overlap.conflict_details:
        all_paths = [d.path for d in overlap.conflict_details]
        common_prefix = find_common_prefix(all_paths)
        if common_prefix:
            lines.append(f"  - 📁 `{common_prefix}`")
        for detail in overlap.conflict_details:
            display_path = detail.path[len(common_prefix):] if common_prefix else detail.path
            size_str = format_conflict_size(detail)
            lines.append(f"    - `{display_path}`{size_str}")
    elif overlap.conflict_files:
        common_prefix = find_common_prefix(overlap.conflict_files)
        if common_prefix:
            lines.append(f"  - 📁 `{common_prefix}`")
        for f in overlap.conflict_files:
            display_path = f[len(common_prefix):] if common_prefix else f
            lines.append(f"    - `{display_path}`")