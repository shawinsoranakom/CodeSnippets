async def _handle_glob(args: dict[str, Any]) -> dict[str, Any]:
    """Find files matching a name pattern inside the sandbox using ``find``."""
    if not args:
        return _mcp(
            "Your glob call had empty arguments \u2014 this means your previous "
            "response was too long and the tool call was truncated by the API. "
            "Break your work into smaller steps.",
            error=True,
        )
    pattern: str = args.get("pattern", "")
    path: str = args.get("path", "")

    if not pattern:
        return _mcp("pattern is required", error=True)

    sandbox = _get_sandbox()
    if sandbox is None:
        return _mcp("No E2B sandbox available", error=True)

    try:
        search_dir = resolve_sandbox_path(path) if path else E2B_WORKDIR
    except ValueError as exc:
        return _mcp(str(exc), error=True)

    cmd = f"find {shlex.quote(search_dir)} -name {shlex.quote(pattern)} -type f 2>/dev/null | head -500"
    try:
        result = await sandbox.commands.run(cmd, cwd=E2B_WORKDIR, timeout=10)
    except Exception as exc:
        return _mcp(f"Glob failed: {exc}", error=True)

    files = [line for line in (result.stdout or "").strip().splitlines() if line]
    return _mcp(json.dumps(files, indent=2))