def get_git_changes(cwd: str) -> list[dict[str, str]]:
    git_dirs = {
        os.path.dirname(f)[2:]
        for f in glob.glob('./*/.git', root_dir=cwd, recursive=True)
    }

    # First try the workspace directory
    changes = get_changes_in_repo(cwd)

    # Filter out any changes which are in one of the git directories
    changes = [
        change
        for change in changes
        if next(
            iter(git_dir for git_dir in git_dirs if change['path'].startswith(git_dir)),
            None,
        )
        is None
    ]

    # Add changes from git directories
    for git_dir in git_dirs:
        git_dir_changes = get_changes_in_repo(str(Path(cwd, git_dir)))
        for change in git_dir_changes:
            change['path'] = git_dir + '/' + change['path']
            changes.append(change)

    changes.sort(key=lambda change: change['path'])

    return changes