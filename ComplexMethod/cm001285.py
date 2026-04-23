async def upload_file(
    user_id: Annotated[str, fastapi.Security(get_user_id)],
    file: UploadFile,
    session_id: str | None = Query(default=None),
    overwrite: bool = Query(default=False),
) -> UploadFileResponse:
    """
    Upload a file to the user's workspace.

    Files are stored in session-scoped paths when session_id is provided,
    so the agent's session-scoped tools can discover them automatically.
    """
    # Empty-string session_id drops session scoping; normalize to None.
    session_id = session_id or None

    config = Config()

    # Sanitize filename — strip any directory components
    filename = os.path.basename(file.filename or "upload") or "upload"

    # Read file content with early abort on size limit
    max_file_bytes = config.max_file_size_mb * 1024 * 1024
    chunks: list[bytes] = []
    total_size = 0
    while chunk := await file.read(64 * 1024):  # 64KB chunks
        total_size += len(chunk)
        if total_size > max_file_bytes:
            raise fastapi.HTTPException(
                status_code=413,
                detail=f"File exceeds maximum size of {config.max_file_size_mb} MB",
            )
        chunks.append(chunk)
    content = b"".join(chunks)

    # Get or create workspace
    workspace = await get_or_create_workspace(user_id)

    # Pre-write storage cap check (soft check — final enforcement is post-write)
    storage_limit_bytes = config.max_workspace_storage_mb * 1024 * 1024
    current_usage = await get_workspace_total_size(workspace.id)
    if storage_limit_bytes and current_usage + len(content) > storage_limit_bytes:
        used_percent = (current_usage / storage_limit_bytes) * 100
        raise fastapi.HTTPException(
            status_code=413,
            detail={
                "message": "Storage limit exceeded",
                "used_bytes": current_usage,
                "limit_bytes": storage_limit_bytes,
                "used_percent": round(used_percent, 1),
            },
        )

    # Warn at 80% usage
    if (
        storage_limit_bytes
        and (usage_ratio := (current_usage + len(content)) / storage_limit_bytes) >= 0.8
    ):
        logger.warning(
            f"User {user_id} workspace storage at {usage_ratio * 100:.1f}% "
            f"({current_usage + len(content)} / {storage_limit_bytes} bytes)"
        )

    # Virus scan
    await scan_content_safe(content, filename=filename)

    # Write file via WorkspaceManager
    manager = WorkspaceManager(user_id, workspace.id, session_id)
    try:
        workspace_file = await manager.write_file(
            content, filename, overwrite=overwrite, metadata={"origin": "user-upload"}
        )
    except ValueError as e:
        # write_file raises ValueError for both path-conflict and size-limit
        # cases; map each to its correct HTTP status.
        message = str(e)
        if message.startswith("File too large"):
            raise fastapi.HTTPException(status_code=413, detail=message) from e
        raise fastapi.HTTPException(status_code=409, detail=message) from e

    # Post-write storage check — eliminates TOCTOU race on the quota.
    # If a concurrent upload pushed us over the limit, undo this write.
    new_total = await get_workspace_total_size(workspace.id)
    if storage_limit_bytes and new_total > storage_limit_bytes:
        try:
            await soft_delete_workspace_file(workspace_file.id, workspace.id)
        except Exception as e:
            logger.warning(
                f"Failed to soft-delete over-quota file {workspace_file.id} "
                f"in workspace {workspace.id}: {e}"
            )
        raise fastapi.HTTPException(
            status_code=413,
            detail={
                "message": "Storage limit exceeded (concurrent upload)",
                "used_bytes": new_total,
                "limit_bytes": storage_limit_bytes,
            },
        )

    return UploadFileResponse(
        file_id=workspace_file.id,
        name=workspace_file.name,
        path=workspace_file.path,
        mime_type=workspace_file.mime_type,
        size_bytes=workspace_file.size_bytes,
    )