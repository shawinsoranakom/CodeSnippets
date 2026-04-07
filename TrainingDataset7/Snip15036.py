def delete_remote_and_local_branch(checkout_dir, branch, *, dry_run=True):
    """Delete a remote branch from origin and the maching local branch."""
    try:
        run(
            ["git", "branch", "-D", branch],
            cwd=checkout_dir,
            dry_run=dry_run,
        )
    except subprocess.CalledProcessError:
        print(f"[ERROR] Local branch {branch} can not be deleted.")

    run(
        ["git", "push", "origin", "--delete", branch.replace("origin/", "", 1)],
        cwd=checkout_dir,
        dry_run=dry_run,
    )