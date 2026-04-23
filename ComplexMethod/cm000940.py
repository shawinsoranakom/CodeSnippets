async def _handle_edit_file(args: dict[str, Any]) -> dict[str, Any]:
    """Replace a substring in a file — E2B sandbox or local SDK working directory."""
    if not args:
        return _mcp(
            "Your Edit call had empty arguments \u2014 this means your previous "
            "response was too long and the tool call was truncated by the API. "
            "Break your work into smaller steps.",
            error=True,
        )
    file_path: str = args.get("file_path", "")
    old_string: str = args.get("old_string", "")
    new_string: str = args.get("new_string", "")
    replace_all: bool = args.get("replace_all", False)

    # Partial truncation: file_path missing but edit strings present
    if not file_path:
        if old_string or new_string:
            return _mcp(_EDIT_PARTIAL_TRUNCATION_MSG, error=True)
        return _mcp(
            "Your Edit call had empty arguments \u2014 this means your previous "
            "response was too long and the tool call was truncated by the API. "
            "Break your work into smaller steps.",
            error=True,
        )

    if not old_string:
        return _mcp("old_string is required", error=True)

    sandbox = _get_sandbox()
    if sandbox is not None:
        # E2B path — edit in sandbox filesystem
        try:
            remote = resolve_sandbox_path(file_path)
        except ValueError as exc:
            return _mcp(str(exc), error=True)

        parent = os.path.dirname(remote)
        canonical_parent = await _check_sandbox_symlink_escape(sandbox, parent)
        if canonical_parent is None:
            return _mcp(
                f"Path must be within {E2B_ALLOWED_DIRS_STR}: {os.path.basename(parent)}",
                error=True,
            )
        remote = os.path.join(canonical_parent, os.path.basename(remote))

        try:
            raw = bytes(await sandbox.files.read(remote, format="bytes"))
            content = raw.decode("utf-8", errors="replace")
        except Exception as exc:
            return _mcp(f"Failed to read {os.path.basename(remote)}: {exc}", error=True)

        count = content.count(old_string)
        if count == 0:
            return _mcp(f"old_string not found in {file_path}", error=True)
        if count > 1 and not replace_all:
            return _mcp(
                f"old_string appears {count} times in {file_path}. "
                "Use replace_all=true or provide a more unique string.",
                error=True,
            )

        updated = (
            content.replace(old_string, new_string)
            if replace_all
            else content.replace(old_string, new_string, 1)
        )
        try:
            await _sandbox_write(sandbox, remote, updated)
        except Exception as exc:
            return _mcp(
                f"Failed to write {os.path.basename(remote)}: {exc}", error=True
            )

        return _mcp(
            f"Edited {file_path} ({count} replacement{'s' if count > 1 else ''})"
        )

    # Non-E2B path — edit in SDK working directory
    sdk_cwd = get_sdk_cwd()
    if not sdk_cwd:
        return _mcp("No SDK working directory available", error=True)

    resolved, err = _resolve_and_validate(file_path, sdk_cwd)
    if err is not None:
        return err
    assert resolved is not None

    # Per-path lock prevents parallel edits from racing through
    # the read-modify-write cycle and silently dropping changes.
    # LRU-bounded: evict the oldest entry when the dict is full so that
    # _edit_locks does not grow unboundedly in long-running server processes.
    if resolved not in _edit_locks:
        if len(_edit_locks) >= _EDIT_LOCKS_MAX:
            _edit_locks.popitem(last=False)
        _edit_locks[resolved] = asyncio.Lock()
    else:
        _edit_locks.move_to_end(resolved)
    lock = _edit_locks[resolved]
    async with lock:
        try:
            with open(resolved, encoding="utf-8") as f:
                content = f.read()
        except FileNotFoundError:
            return _mcp(f"File not found: {file_path}", error=True)
        except PermissionError:
            return _mcp(f"Permission denied: {file_path}", error=True)
        except Exception as exc:
            return _mcp(f"Failed to read {file_path}: {exc}", error=True)

        count = content.count(old_string)
        if count == 0:
            return _mcp(f"old_string not found in {file_path}", error=True)
        if count > 1 and not replace_all:
            return _mcp(
                f"old_string appears {count} times in {file_path}. "
                "Use replace_all=true or provide a more unique string.",
                error=True,
            )

        updated = (
            content.replace(old_string, new_string)
            if replace_all
            else content.replace(old_string, new_string, 1)
        )

        # Yield to the event loop between the read and write phases so other
        # coroutines waiting on this lock can be scheduled.  The lock above
        # ensures they cannot enter the critical section until we release it.
        await asyncio.sleep(0)

        try:
            with open(resolved, "w", encoding="utf-8") as f:
                f.write(updated)
        except Exception as exc:
            return _mcp(f"Failed to write {file_path}: {exc}", error=True)

    return _mcp(f"Edited {file_path} ({count} replacement{'s' if count > 1 else ''})")