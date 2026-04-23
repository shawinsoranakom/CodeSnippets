def find_file_overlap_candidates(
    current_files: list[str],
    other_prs: list[dict],
    max_age_days: int = 14
) -> list[tuple[dict, list[str]]]:
    """Find PRs that share files with the current PR."""
    from datetime import datetime, timezone, timedelta

    current_files_set = set(f for f in current_files if not should_ignore_file(f))
    candidates = []
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=max_age_days)

    for pr_data in other_prs:
        # Filter out PRs older than max_age_days
        updated_at = pr_data.get("updated_at")
        if updated_at:
            try:
                pr_date = datetime.fromisoformat(updated_at.replace('Z', '+00:00'))
                if pr_date < cutoff_date:
                    continue  # Skip old PRs
            except Exception as e:
                # If we can't parse date, include the PR (safe fallback)
                print(f"Warning: Could not parse date for PR: {e}", file=sys.stderr)

        other_files = set(f for f in pr_data["files"] if not should_ignore_file(f))
        shared = current_files_set & other_files

        if shared:
            candidates.append((pr_data, list(shared)))

    return candidates