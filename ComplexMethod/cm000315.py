def find_line_overlaps(
    changes_a: dict[str, "ChangedFile"],
    changes_b: dict[str, "ChangedFile"],
    shared_files: list[str]
) -> dict[str, list[tuple[int, int]]]:
    """Find overlapping line ranges in shared files."""
    overlaps = {}

    for file_path in shared_files:
        if should_ignore_file(file_path):
            continue

        file_a = changes_a.get(file_path)
        file_b = changes_b.get(file_path)

        if not file_a or not file_b:
            continue

        # Skip pure renames
        if file_a.is_rename and not file_a.additions and not file_a.deletions:
            continue
        if file_b.is_rename and not file_b.additions and not file_b.deletions:
            continue

        # Note: This mixes old-file (deletions) and new-file (additions) line numbers,
        # which can cause false positives when PRs insert/remove many lines.
        # Acceptable for v1 since the real merge test is the authoritative check.
        file_overlaps = find_range_overlaps(
            file_a.additions + file_a.deletions,
            file_b.additions + file_b.deletions
        )

        if file_overlaps:
            overlaps[file_path] = merge_ranges(file_overlaps)

    return overlaps