async def _read_file_handler(args: dict[str, Any]) -> dict[str, Any]:
    """Read a file with optional offset/limit.

    Supports ``workspace://`` URIs (delegated to the workspace manager) and
    local paths within the session's allowed directories (sdk_cwd + tool-results).
    """

    def _mcp_err(text: str) -> dict[str, Any]:
        return {"content": [{"type": "text", "text": text}], "isError": True}

    def _mcp_ok(text: str) -> dict[str, Any]:
        return {"content": [{"type": "text", "text": text}], "isError": False}

    if not args:
        return _mcp_err(
            "Your Read call had empty arguments \u2014 this means your previous "
            "response was too long and the tool call was truncated by the API. "
            "Break your work into smaller steps."
        )

    file_path = args.get("file_path", "")
    try:
        offset = max(0, int(args.get("offset", 0)))
        limit = max(1, int(args.get("limit", 2000)))
    except (ValueError, TypeError):
        return _mcp_err("Invalid offset/limit \u2014 must be integers.")

    if not file_path:
        if "offset" in args or "limit" in args:
            return _mcp_err(
                "Your Read call was truncated (file_path missing but "
                "offset/limit were present). Resend with the full file_path."
            )
        return _mcp_err("file_path is required")

    if file_path.startswith("workspace://"):
        user_id, session = get_execution_context()
        if session is None:
            return _mcp_err("workspace:// file references require an active session")
        try:
            raw = await read_file_bytes(file_path, user_id, session)
        except ValueError as exc:
            return _mcp_err(str(exc))
        lines = raw.decode("utf-8", errors="replace").splitlines(keepends=True)
        selected = list(itertools.islice(lines, offset, offset + limit))
        numbered = "".join(
            f"{i + offset + 1:>6}\t{line}" for i, line in enumerate(selected)
        )
        return _mcp_ok(numbered)

    # Use is_sdk_tool_path (not is_allowed_local_path) to restrict this tool
    # to only SDK-internal tool-results/tool-outputs paths.  is_sdk_tool_path
    # validates session membership via _current_project_dir, preventing
    # cross-session reads.  sdk_cwd files (workspace outputs) are NOT allowed
    # here — they are served by the e2b_file_tools Read handler instead.
    if not is_sdk_tool_path(file_path):
        return _mcp_err(f"Path not allowed: {os.path.basename(file_path)}")

    resolved = os.path.realpath(os.path.expanduser(file_path))
    try:
        with open(resolved, encoding="utf-8", errors="replace") as f:
            selected = list(itertools.islice(f, offset, offset + limit))
        # Cleanup happens in _cleanup_sdk_tool_results after session ends;
        # don't delete here — the SDK may read in multiple chunks.
        #
        # When E2B is active, also copy the file into the sandbox so
        # bash_exec can process it (the model often uses Read then bash).
        text = "".join(selected)
        sandbox = _current_sandbox.get(None)
        if sandbox is not None:
            annotation = await bridge_and_annotate(sandbox, resolved, offset, limit)
            if annotation:
                text += annotation
        return _mcp_ok(text)
    except FileNotFoundError:
        return _mcp_err(f"File not found: {file_path}")
    except Exception as e:
        return _mcp_err(f"Error reading file: {e}")