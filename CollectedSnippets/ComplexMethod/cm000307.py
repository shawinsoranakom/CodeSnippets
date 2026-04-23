def run_batch_merge_tests(
    owner: str,
    repo: str,
    base_branch: str,
    current_pr: "PullRequest",
    overlaps: list["Overlap"]
):
    """Run merge tests for multiple PRs using a shared clone."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Clone once
        if not clone_repo(owner, repo, base_branch, tmpdir):
            return

        configure_git(tmpdir)

        # Fetch current PR branch once
        result = run_git(["fetch", "origin", f"pull/{current_pr.number}/head:pr-{current_pr.number}"], cwd=tmpdir, check=False)
        if result.returncode != 0:
            print(f"Warning: Could not fetch current PR #{current_pr.number}", file=sys.stderr)
            return

        for overlap in overlaps:
            other_pr = overlap.pr_b if overlap.pr_a.number == current_pr.number else overlap.pr_a
            print(f"Testing merge conflict with PR #{other_pr.number}...", flush=True)

            # Clean up any in-progress merge from previous iteration
            run_git(["merge", "--abort"], cwd=tmpdir, check=False)

            # Reset to base branch
            run_git(["checkout", base_branch], cwd=tmpdir, check=False)
            run_git(["reset", "--hard", f"origin/{base_branch}"], cwd=tmpdir, check=False)
            run_git(["clean", "-fdx"], cwd=tmpdir, check=False)

            # Fetch the other PR branch
            result = run_git(["fetch", "origin", f"pull/{other_pr.number}/head:pr-{other_pr.number}"], cwd=tmpdir, check=False)
            if result.returncode != 0:
                print(f"Warning: Could not fetch PR #{other_pr.number}: {result.stderr.strip()}", file=sys.stderr)
                continue

            # Try merging current PR first
            result = run_git(["merge", "--no-commit", "--no-ff", f"pr-{current_pr.number}"], cwd=tmpdir, check=False)
            if result.returncode != 0:
                # Current PR conflicts with base
                conflict_files, conflict_details = extract_conflict_info(tmpdir, result.stderr)
                overlap.has_merge_conflict = True
                overlap.conflict_files = conflict_files
                overlap.conflict_details = conflict_details
                overlap.conflict_type = 'pr_a_conflicts_base'
                run_git(["merge", "--abort"], cwd=tmpdir, check=False)
                continue

            # Commit and try merging other PR
            run_git(["commit", "-m", f"Merge PR #{current_pr.number}"], cwd=tmpdir, check=False)

            result = run_git(["merge", "--no-commit", "--no-ff", f"pr-{other_pr.number}"], cwd=tmpdir, check=False)
            if result.returncode != 0:
                # Conflict between PRs
                conflict_files, conflict_details = extract_conflict_info(tmpdir, result.stderr)
                overlap.has_merge_conflict = True
                overlap.conflict_files = conflict_files
                overlap.conflict_details = conflict_details
                overlap.conflict_type = 'conflict'
                run_git(["merge", "--abort"], cwd=tmpdir, check=False)