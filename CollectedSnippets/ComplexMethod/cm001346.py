def vcs_state_diverges_from_master() -> bool:
    """
    Returns whether a git repo is present and contains changes that are not in `master`.
    """
    paths_we_care_about = "classic/original_autogpt/classic/original_autogpt/**/*.py"
    try:
        repo = Repo(search_parent_directories=True)

        # Check for uncommitted changes in the specified path
        uncommitted_changes = repo.index.diff(None, paths=paths_we_care_about)
        if uncommitted_changes:
            return True

        # Find OG AutoGPT remote
        for remote in repo.remotes:
            if remote.url.endswith(
                tuple(
                    # All permutations of old/new repo name and HTTP(S)/Git URLs
                    f"{prefix}{path}"
                    for prefix in ("://github.com/", "git@github.com:")
                    for path in (
                        f"Significant-Gravitas/{n}.git" for n in ("AutoGPT", "Auto-GPT")
                    )
                )
            ):
                og_remote = remote
                break
        else:
            # Original AutoGPT remote is not configured: assume local codebase diverges
            return True

        master_branch = og_remote.refs.master
        with contextlib.suppress(StopIteration):
            next(repo.iter_commits(f"HEAD..{master_branch}", paths=paths_we_care_about))
            # Local repo is one or more commits ahead of OG AutoGPT master branch
            return True

        # Relevant part of the codebase is on master
        return False
    except InvalidGitRepositoryError:
        # No git repo present: assume codebase is a clean download
        return False