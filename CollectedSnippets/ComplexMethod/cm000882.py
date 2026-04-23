def _validate_workspace_path(
    tool_name: str, tool_input: dict[str, Any], sdk_cwd: str | None
) -> dict[str, Any]:
    """Validate that a workspace-scoped tool only accesses allowed paths.

    For ``Read``: only SDK artifact paths (tool-results/, tool-outputs/) are
    permitted.  The workspace directory is served by the ``read_file`` MCP
    tool which enforces per-session isolation.

    For ``Glob`` / ``Grep``: the full workspace (sdk_cwd) is allowed in
    addition to SDK artifact paths.
    """
    path = tool_input.get("file_path") or tool_input.get("path") or ""
    if not path:
        # Glob/Grep without a path default to cwd which is already sandboxed
        return {}

    if tool_name == "Read":
        # Narrow carve-out: only allow SDK artifact paths for the native Read tool.
        # ``is_sdk_tool_path`` validates session membership via _current_project_dir,
        # preventing cross-session access to another session's tool-results directory.
        # All other file reads must go through the read_file MCP tool.
        if is_sdk_tool_path(path):
            return {}
        logger.warning(f"Blocked Read outside SDK artifact paths: {path}")
        return _deny(
            "[SECURITY] The SDK 'Read' tool can only access tool-results/ or "
            "tool-outputs/ paths. Use the 'read_file' MCP tool to read workspace files. "
            "This is enforced by the platform and cannot be bypassed."
        )

    if is_allowed_local_path(path, sdk_cwd):
        return {}

    logger.warning(f"Blocked {tool_name} outside workspace: {path}")
    workspace_hint = f" Allowed workspace: {sdk_cwd}" if sdk_cwd else ""
    return _deny(
        f"[SECURITY] Tool '{tool_name}' can only access files within the workspace "
        f"directory.{workspace_hint} "
        "This is enforced by the platform and cannot be bypassed."
    )