def find_overlapping_prs(
    owner: str,
    repo: str,
    base_branch: str,
    current_pr: "PullRequest",
    current_pr_number: int,
    skip_merge_test: bool
) -> tuple[list["Overlap"], dict[int, dict[str, "ChangedFile"]]]:
    """Find all PRs that overlap with the current PR."""
    # Query other open PRs
    all_prs = query_open_prs(owner, repo, base_branch)
    other_prs = [p for p in all_prs if p["number"] != current_pr_number]

    print(f"Found {len(other_prs)} other open PRs targeting {base_branch}")

    # Find file overlaps (excluding ignored files, filtering by age)
    candidates = find_file_overlap_candidates(current_pr.files, other_prs)

    print(f"Found {len(candidates)} PRs with file overlap (excluding ignored files)")

    if not candidates:
        return [], {}

    # First pass: analyze line overlaps (no merge testing yet)
    overlaps = []
    all_changes = {}
    prs_needing_merge_test = []

    for pr_data, shared_files in candidates:
        overlap, pr_changes = analyze_pr_overlap(
            owner, repo, base_branch, current_pr, pr_data, shared_files,
            skip_merge_test=True  # Always skip in first pass
        )
        if overlap:
            overlaps.append(overlap)
            all_changes[pr_data["number"]] = pr_changes
            # Track PRs that need merge testing
            if overlap.line_overlaps and not skip_merge_test:
                prs_needing_merge_test.append(overlap)

    # Second pass: batch merge testing with shared clone
    if prs_needing_merge_test:
        run_batch_merge_tests(owner, repo, base_branch, current_pr, prs_needing_merge_test)

    return overlaps, all_changes