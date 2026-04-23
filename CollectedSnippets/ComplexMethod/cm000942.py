async def _handle_grep(args: dict[str, Any]) -> dict[str, Any]:
    """Search file contents by regex inside the sandbox using ``grep -rn``."""
    if not args:
        return _mcp(
            "Your grep call had empty arguments \u2014 this means your previous "
            "response was too long and the tool call was truncated by the API. "
            "Break your work into smaller steps.",
            error=True,
        )
    pattern: str = args.get("pattern", "")
    path: str = args.get("path", "")
    include: str = args.get("include", "")

    if not pattern:
        return _mcp("pattern is required", error=True)

    sandbox = _get_sandbox()
    if sandbox is None:
        return _mcp("No E2B sandbox available", error=True)

    try:
        search_dir = resolve_sandbox_path(path) if path else E2B_WORKDIR
    except ValueError as exc:
        return _mcp(str(exc), error=True)

    parts = ["grep", "-rn", "--color=never"]
    if include:
        parts.extend(["--include", include])
    parts.extend([pattern, search_dir])
    cmd = " ".join(shlex.quote(p) for p in parts) + " 2>/dev/null | head -200"

    try:
        result = await sandbox.commands.run(cmd, cwd=E2B_WORKDIR, timeout=15)
    except Exception as exc:
        return _mcp(f"Grep failed: {exc}", error=True)

    output = (result.stdout or "").strip()
    return _mcp(output if output else "No matches found.")