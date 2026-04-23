def is_allowed_local_path(path: str, sdk_cwd: str | None = None) -> bool:
    """Return True if *path* is within an allowed host-filesystem location.

    Allowed:
    - Files under *sdk_cwd* (``/tmp/copilot-<session>/``)
    - Files under ``~/.claude/projects/<encoded-cwd>/<uuid>/tool-results/...``
      or ``tool-outputs/...``.
      The SDK nests tool-results under a conversation UUID directory;
      the UUID segment is validated with ``_UUID_RE``.
    """
    if not path:
        return False

    if path.startswith("~"):
        resolved = os.path.realpath(os.path.expanduser(path))
    elif not os.path.isabs(path) and sdk_cwd:
        resolved = os.path.realpath(os.path.join(sdk_cwd, path))
    else:
        resolved = os.path.realpath(path)

    if sdk_cwd:
        norm_cwd = os.path.realpath(sdk_cwd)
        if resolved == norm_cwd or resolved.startswith(norm_cwd + os.sep):
            return True

    encoded = _current_project_dir.get("")
    if encoded:
        project_dir = os.path.realpath(os.path.join(SDK_PROJECTS_DIR, encoded))
        # Defence-in-depth: ensure project_dir didn't escape the base.
        if not project_dir.startswith(SDK_PROJECTS_DIR + os.sep):
            return False
        # Only allow: <encoded-cwd>/<uuid>/<tool-dir>/<file>
        # The SDK always creates a conversation UUID directory between
        # the project dir and the tool directory.
        # Accept both "tool-results" (SDK's persisted outputs) and
        # "tool-outputs" (the model sometimes confuses workspace paths
        # with filesystem paths and generates this variant).
        if resolved.startswith(project_dir + os.sep):
            relative = resolved[len(project_dir) + 1 :]
            parts = relative.split(os.sep)
            # Require exactly: [<uuid>, "tool-results"|"tool-outputs", <file>, ...]
            if (
                len(parts) >= 3
                and _UUID_RE.match(parts[0])
                and parts[1] in ("tool-results", "tool-outputs")
            ):
                return True

    return False