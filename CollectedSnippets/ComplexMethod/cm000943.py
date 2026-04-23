async def bridge_to_sandbox(
    sandbox: Any, file_path: str, offset: int, limit: int
) -> str | None:
    """Best-effort copy of a host-side SDK file into the E2B sandbox.

    When the model reads an SDK-internal file (e.g. tool-results), it often
    wants to process the data with bash.  Copying the file into the sandbox
    under a stable name lets ``bash_exec`` access it without extra steps.

    Only copies when offset=0 and limit is large enough to indicate the model
    wants the full file.  Errors are logged but never propagated.

    Returns the sandbox path on success, or ``None`` on skip/failure.

    Size handling:
    - <= 32 KB: written to ``/tmp/<hash>-<basename>`` via shell base64
      (``_sandbox_write``).  Kept small to stay within ARG_MAX.
    - 32 KB - 50 MB: written to ``/home/user/<hash>-<basename>`` via
      ``sandbox.files.write()`` to avoid shell argument length limits.
    - > 50 MB: skipped entirely with a warning.

    The sandbox filename is prefixed with a short hash of the full source
    path to avoid collisions when different source files share the same
    basename (e.g. multiple ``result.json`` files).
    """
    if offset != 0 or limit < _DEFAULT_READ_LIMIT:
        return None
    try:
        expanded = os.path.realpath(os.path.expanduser(file_path))
        basename = os.path.basename(expanded)
        source_id = hashlib.sha256(expanded.encode()).hexdigest()[:12]
        unique_name = f"{source_id}-{basename}"
        file_size = os.path.getsize(expanded)
        if file_size > _BRIDGE_SKIP_BYTES:
            logger.warning(
                "[E2B] Skipping bridge for large file (%d bytes): %s",
                file_size,
                basename,
            )
            return None

        def _read_bytes() -> bytes:
            with open(expanded, "rb") as fh:
                return fh.read()

        raw_content = await asyncio.to_thread(_read_bytes)
        try:
            text_content: str | None = raw_content.decode("utf-8")
        except UnicodeDecodeError:
            text_content = None
        data: str | bytes = text_content if text_content is not None else raw_content
        if file_size <= _BRIDGE_SHELL_MAX_BYTES:
            sandbox_path = f"/tmp/{unique_name}"
            await _sandbox_write(sandbox, sandbox_path, data)
        else:
            sandbox_path = f"/home/user/{unique_name}"
            await sandbox.files.write(sandbox_path, data)
        logger.info(
            "[E2B] Bridged SDK file to sandbox: %s -> %s", basename, sandbox_path
        )
        return sandbox_path
    except Exception:
        logger.warning(
            "[E2B] Failed to bridge SDK file to sandbox: %s",
            file_path,
            exc_info=True,
        )
        return None