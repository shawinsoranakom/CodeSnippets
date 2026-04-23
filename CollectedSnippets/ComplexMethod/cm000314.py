def classify_overlap_risk(
    overlap: "Overlap",
    changes_a: dict[str, "ChangedFile"],
    changes_b: dict[str, "ChangedFile"]
) -> str:
    """Classify the risk level of an overlap."""
    if overlap.has_merge_conflict:
        return 'conflict'

    has_rename = any(
        (changes_a.get(f) and changes_a[f].is_rename) or 
        (changes_b.get(f) and changes_b[f].is_rename)
        for f in overlap.overlapping_files
    )

    if overlap.line_overlaps:
        total_overlap_lines = sum(
            end - start + 1
            for ranges in overlap.line_overlaps.values()
            for start, end in ranges
        )

        # Medium risk: >20 lines overlap or file rename
        if total_overlap_lines > 20 or has_rename:
            return 'medium'
        else:
            return 'low'

    if has_rename:
        return 'medium'

    return 'low'