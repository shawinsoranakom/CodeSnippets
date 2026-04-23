def get_branch_info(checkout_dir, branch):
    """Return (commit_hash, last_update_date) for a given branch."""
    commit_hash = run(["git", "rev-parse", branch], cwd=checkout_dir, dry_run=False)
    last_update = run(
        ["git", "show", branch, "--format=format:%ai", "-s"],
        cwd=checkout_dir,
        dry_run=False,
    )
    return commit_hash, last_update