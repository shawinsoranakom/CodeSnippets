def get_remote_branches(checkout_dir, include_fn):
    """Return list of remote branches filtered by include_fn."""
    result = run(
        ["git", "branch", "--list", "-r"],
        cwd=checkout_dir,
        dry_run=False,
    )
    branches = [b.strip() for b in result.split("\n") if b.strip()]
    return [b for b in branches if include_fn(b)]