def is_sdk_tool_path(path: str) -> bool:
    """Return True if *path* is an SDK-internal tool-results or tool-outputs path.

    These paths exist on the host filesystem (not in the E2B sandbox) and are
    created by the Claude Agent SDK itself.  In E2B mode, only these paths should
    be read from the host; all other paths should be read from the sandbox.

    This is a strict subset of ``is_allowed_local_path`` — it intentionally
    excludes ``sdk_cwd`` paths because those are the agent's working directory,
    which in E2B mode is the sandbox, not the host.
    """
    if not path:
        return False

    if path.startswith("~"):
        resolved = os.path.realpath(os.path.expanduser(path))
    elif not os.path.isabs(path):
        # Relative paths cannot resolve to an absolute SDK-internal path
        return False
    else:
        resolved = os.path.realpath(path)

    encoded = _current_project_dir.get("")
    if not encoded:
        return False

    project_dir = os.path.realpath(os.path.join(SDK_PROJECTS_DIR, encoded))
    if not project_dir.startswith(SDK_PROJECTS_DIR + os.sep):
        return False
    if not resolved.startswith(project_dir + os.sep):
        return False

    relative = resolved[len(project_dir) + 1 :]
    parts = relative.split(os.sep)
    return (
        len(parts) >= 3
        and _UUID_RE.match(parts[0]) is not None
        and parts[1] in ("tool-results", "tool-outputs")
    )