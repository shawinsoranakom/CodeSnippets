def create_tag(checkout_dir, branch, commit_hash, last_update, *, dry_run=True):
    """Create a tag locally for a given branch at its last update."""
    tag_name = branch.replace("origin/", "", 1)
    msg = f'"Tagged {tag_name} for EOL stable branch removal."'
    run(
        ["git", "tag", "--sign", "--message", msg, tag_name, commit_hash],
        cwd=checkout_dir,
        env={"GIT_COMMITTER_DATE": last_update},
        dry_run=dry_run,
    )
    return tag_name