async def _handle_write_file(args: dict[str, Any]) -> dict[str, Any]:
    """Write content to a file — E2B sandbox or local SDK working directory."""
    if not args:
        return _mcp(_COMPLETE_TRUNCATION_MSG, error=True)
    file_path: str = args.get("file_path", "")
    content: str = args.get("content", "")

    truncation_err = _check_truncation(file_path, content)
    if truncation_err is not None:
        return truncation_err

    sandbox = _get_sandbox()
    if sandbox is not None:
        # E2B path — write to sandbox filesystem
        try:
            remote = resolve_sandbox_path(file_path)
        except ValueError as exc:
            return _mcp(str(exc), error=True)

        try:
            parent = os.path.dirname(remote)
            if parent and parent not in E2B_ALLOWED_DIRS:
                await sandbox.files.make_dir(parent)
            canonical_parent = await _check_sandbox_symlink_escape(sandbox, parent)
            if canonical_parent is None:
                return _mcp(
                    f"Path must be within {E2B_ALLOWED_DIRS_STR}: {os.path.basename(parent)}",
                    error=True,
                )
            remote = os.path.join(canonical_parent, os.path.basename(remote))
            await _sandbox_write(sandbox, remote, content)
        except Exception as exc:
            return _mcp(
                f"Failed to write {os.path.basename(remote)}: {exc}", error=True
            )

        msg = f"Successfully wrote to {file_path}"
        if len(content) > _LARGE_CONTENT_WARN_CHARS:
            logger.warning(
                "[Write] large inline content (%d chars) for %s",
                len(content),
                remote,
            )
            msg += (
                f"\n\nWARNING: The content was very large ({len(content)} chars). "
                "Next time, write large files in sections using bash_exec with "
                "'cat > file << EOF ... EOF' and 'cat >> file << EOF ... EOF' "
                "to avoid output-token truncation."
            )
        return _mcp(msg)

    # Non-E2B path — write to SDK working directory
    sdk_cwd = get_sdk_cwd()
    if not sdk_cwd:
        return _mcp("No SDK working directory available", error=True)

    resolved, err = _resolve_and_validate(file_path, sdk_cwd)
    if err is not None:
        return err
    assert resolved is not None

    try:
        parent = os.path.dirname(resolved)
        if parent:
            os.makedirs(parent, exist_ok=True)
        with open(resolved, "w", encoding="utf-8") as f:
            f.write(content)
    except Exception as exc:
        logger.error("Write failed for %s: %s", resolved, exc, exc_info=True)
        return _mcp(
            f"Failed to write {os.path.basename(resolved)}: {type(exc).__name__}",
            error=True,
        )

    msg = f"Successfully wrote to {file_path}"
    if len(content) > _LARGE_CONTENT_WARN_CHARS:
        logger.warning(
            "[Write] large inline content (%d chars) for %s",
            len(content),
            resolved,
        )
        msg += (
            f"\n\nWARNING: The content was very large ({len(content)} chars). "
            "Next time, write large files in sections using bash_exec with "
            "'cat > file << EOF ... EOF' and 'cat >> file << EOF ... EOF' "
            "to avoid output-token truncation."
        )
    return _mcp(msg)