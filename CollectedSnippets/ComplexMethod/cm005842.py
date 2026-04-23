def _get_main_branch_head() -> str | None:
    """Get the alembic head revision that origin/main is at.

    Uses ``git grep`` to read the ``revision`` and ``down_revision`` variables
    directly from migration files on origin/main, then walks the chain to find
    the head revision.  This avoids relying on filename conventions (which may
    not match the actual revision IDs inside the files) and works regardless of
    whether the branch adds, modifies, or deletes migration files.

    Returns None if git operations fail (e.g. shallow clone without origin/main).
    """
    git = shutil.which("git")
    if git is None:
        return None

    def _git_grep(pattern: str) -> str | None:
        try:
            result = subprocess.run(  # noqa: S603
                [
                    git,
                    "grep",
                    "-h",
                    pattern,
                    "origin/main",
                    "--",
                    "src/backend/base/langflow/alembic/versions/",
                ],
                capture_output=True,
                text=True,
                check=True,
                cwd=_WORKSPACE_ROOT,
            )
        except subprocess.CalledProcessError:
            return None
        except OSError as exc:
            if exc.errno == errno.ENOENT:
                return None
            raise
        return result.stdout

    # Extract all revision IDs from origin/main's migration files
    rev_output = _git_grep("^revision:")
    if not rev_output:
        return None

    main_rev_ids: set[str] = set()
    for line in rev_output.strip().splitlines():
        main_rev_ids.update(_parse_revision_values(line))

    if not main_rev_ids:
        return None

    # Extract all down_revision IDs to determine the chain
    down_output = _git_grep("^down_revision:")
    referenced: set[str] = set()
    if down_output:
        for line in down_output.strip().splitlines():
            referenced.update(_parse_revision_values(line))

    # Head = revisions not referenced as down_revision by any other revision
    heads = main_rev_ids - referenced

    if len(heads) == 1:
        return heads.pop()
    if len(heads) > 1:
        pytest.fail(f"origin/main has {len(heads)} head revisions — migration branches need merging: {heads}")
    return None