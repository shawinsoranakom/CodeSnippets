def _read_local_tool_result(
    path: str,
    char_offset: int,
    char_length: Optional[int],
    session_id: str,
    sdk_cwd: str | None = None,
) -> ToolResponseBase:
    """Read an SDK tool-result file from local disk.

    This is a fallback for when the model mistakenly calls
    ``read_workspace_file`` with an SDK tool-result path that only exists on
    the host filesystem, not in cloud workspace storage.

    Defence-in-depth: validates *path* via :func:`is_allowed_local_path`
    regardless of what the caller has already checked.
    """
    # TOCTOU: path validated then opened separately. Acceptable because
    # the tool-results directory is server-controlled, not user-writable.
    expanded = os.path.realpath(os.path.expanduser(path))
    # Defence-in-depth: re-check with resolved path (caller checked raw path).
    if not is_allowed_local_path(expanded, sdk_cwd or get_sdk_cwd()):
        return ErrorResponse(
            message=f"Path not allowed: {os.path.basename(path)}", session_id=session_id
        )
    try:
        # The 10 MB cap (_MAX_LOCAL_TOOL_RESULT_BYTES) bounds memory usage.
        # Pre-read size check prevents loading files far above the cap;
        # the remaining TOCTOU gap is acceptable for server-controlled paths.
        file_size = os.path.getsize(expanded)
        if file_size > _MAX_LOCAL_TOOL_RESULT_BYTES:
            return ErrorResponse(
                message=(f"File too large: {os.path.basename(path)}"),
                session_id=session_id,
            )

        # Detect binary files: try strict UTF-8 first, fall back to
        # base64-encoding the raw bytes for binary content.
        with open(expanded, "rb") as fh:
            raw = fh.read()
        try:
            text_content = raw.decode("utf-8")
        except UnicodeDecodeError:
            # Binary file — return raw base64, ignore char_offset/char_length
            return WorkspaceFileContentResponse(
                file_id=_LOCAL_TOOL_RESULT_FILE_ID,
                name=os.path.basename(path),
                path=path,
                mime_type=mimetypes.guess_type(path)[0] or "application/octet-stream",
                content_base64=base64.b64encode(raw).decode("ascii"),
                message=(
                    f"Read {file_size:,} bytes (binary) from local tool-result "
                    f"{os.path.basename(path)}"
                ),
                session_id=session_id,
            )

        end = (
            char_offset + char_length if char_length is not None else len(text_content)
        )
        slice_text = text_content[char_offset:end]
    except FileNotFoundError:
        return ErrorResponse(
            message=f"File not found: {os.path.basename(path)}", session_id=session_id
        )
    except Exception as exc:
        return ErrorResponse(
            message=f"Error reading file: {type(exc).__name__}", session_id=session_id
        )

    return WorkspaceFileContentResponse(
        file_id=_LOCAL_TOOL_RESULT_FILE_ID,
        name=os.path.basename(path),
        path=path,
        mime_type=mimetypes.guess_type(path)[0] or "text/plain",
        content_base64=base64.b64encode(slice_text.encode("utf-8")).decode("ascii"),
        message=(
            f"Read chars {char_offset}\u2013{char_offset + len(slice_text)} "
            f"of {len(text_content):,} chars from local tool-result "
            f"{os.path.basename(path)}"
        ),
        session_id=session_id,
    )