async def _handle_read_file(args: dict[str, Any]) -> dict[str, Any]:
    """Read lines from a file — E2B sandbox, local SDK working dir, or SDK-internal paths."""
    if not args:
        return _mcp(
            "Your read_file call had empty arguments \u2014 this means your previous "
            "response was too long and the tool call was truncated by the API. "
            "Break your work into smaller steps.",
            error=True,
        )
    file_path: str = args.get("file_path", "")
    try:
        offset: int = max(0, int(args.get("offset", 0)))
        limit: int = max(1, int(args.get("limit", _DEFAULT_READ_LIMIT)))
    except (ValueError, TypeError):
        return _mcp("Invalid offset/limit \u2014 must be integers.", error=True)

    if not file_path:
        if "offset" in args or "limit" in args:
            return _mcp(
                "Your read_file call was truncated (file_path missing but "
                "offset/limit were present). Resend with the full file_path.",
                error=True,
            )
        return _mcp("file_path is required", error=True)

    # SDK-internal tool-results/tool-outputs paths are on the host filesystem in
    # both E2B and non-E2B mode — always read them locally.
    # When E2B is active, also copy the file into the sandbox so bash_exec can
    # process it further.
    # NOTE: when E2B is active we intentionally use `is_sdk_tool_path` (not
    # `_is_allowed_local`) so that sdk_cwd-relative paths (e.g. "output.txt")
    # are NOT captured here.  In E2B mode the agent's working directory is the
    # sandbox, not sdk_cwd on the host, so relative paths should be read from
    # the sandbox below.
    sandbox_active = _get_sandbox() is not None
    local_check = (
        is_sdk_tool_path(file_path) if sandbox_active else _is_allowed_local(file_path)
    )
    if local_check:
        result = _read_local(file_path, offset, limit)
        if not result.get("isError"):
            sandbox = _get_sandbox()
            if sandbox is not None:
                annotation = await bridge_and_annotate(
                    sandbox, file_path, offset, limit
                )
                if annotation:
                    result["content"][0]["text"] += annotation
        return result

    sandbox = _get_sandbox()
    if sandbox is not None:
        # E2B path — read from sandbox filesystem
        result = _get_sandbox_and_path(file_path)
        if isinstance(result, dict):
            return result
        sandbox, remote = result

        try:
            raw: bytes = await sandbox.files.read(remote, format="bytes")
            content = raw.decode("utf-8", errors="replace")
        except Exception as exc:
            return _mcp(f"Failed to read {os.path.basename(remote)}: {exc}", error=True)

        lines = content.splitlines(keepends=True)
        selected = list(itertools.islice(lines, offset, offset + limit))
        numbered = "".join(
            f"{i + offset + 1:>6}\t{line}" for i, line in enumerate(selected)
        )
        return _mcp(numbered)

    # Non-E2B path — read from SDK working directory
    sdk_cwd = get_sdk_cwd()
    if not sdk_cwd:
        return _mcp("No SDK working directory available", error=True)

    resolved, err = _resolve_and_validate(file_path, sdk_cwd)
    if err is not None:
        return err
    assert resolved is not None

    if _is_likely_binary(resolved):
        return _mcp(
            f"Cannot read binary file: {os.path.basename(resolved)}. "
            "Use bash_exec with 'xxd' or 'file' to inspect binary files.",
            error=True,
        )

    try:
        with open(resolved, encoding="utf-8", errors="replace") as f:
            selected = list(itertools.islice(f, offset, offset + limit))
    except FileNotFoundError:
        return _mcp(f"File not found: {file_path}", error=True)
    except PermissionError:
        return _mcp(f"Permission denied: {file_path}", error=True)
    except Exception as exc:
        return _mcp(f"Failed to read {file_path}: {exc}", error=True)

    numbered = "".join(
        f"{i + offset + 1:>6}\t{line}" for i, line in enumerate(selected)
    )
    return _mcp(numbered)