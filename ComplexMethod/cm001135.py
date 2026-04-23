async def write_file(
        self,
        content: bytes,
        filename: str,
        path: Optional[str] = None,
        mime_type: Optional[str] = None,
        overwrite: bool = False,
        metadata: Optional[dict] = None,
    ) -> WorkspaceFile:
        """
        Write file to workspace.

        When session_id is set, files are written to /sessions/{session_id}/...
        by default. Use explicit /sessions/... paths for cross-session access.

        Args:
            content: File content as bytes
            filename: Filename for the file
            path: Virtual path (defaults to "/{filename}", session-scoped if session_id set)
            mime_type: MIME type (auto-detected if not provided)
            overwrite: Whether to overwrite existing file at path
            metadata: Optional metadata dict (e.g., origin tracking)

        Returns:
            Created WorkspaceFile instance

        Raises:
            ValueError: If file exceeds size limit or path already exists
        """
        # Enforce file size limit
        max_file_size = Config().max_file_size_mb * 1024 * 1024
        if len(content) > max_file_size:
            raise ValueError(
                f"File too large: {len(content)} bytes exceeds "
                f"{Config().max_file_size_mb}MB limit"
            )

        # Scan here — callers must NOT duplicate this scan.
        # WorkspaceManager owns virus scanning for all persisted files.
        await scan_content_safe(content, filename=filename)

        # Determine path with session scoping
        if path is None:
            path = f"/{filename}"
        elif not path.startswith("/"):
            path = f"/{path}"

        # Resolve path with session prefix
        path = self._resolve_path(path)

        # Check if file exists at path (only error for non-overwrite case)
        # For overwrite=True, we let the write proceed and handle via UniqueViolationError
        # This ensures the new file is written to storage BEFORE the old one is deleted,
        # preventing data loss if the new write fails
        db = workspace_db()

        if not overwrite:
            existing = await db.get_workspace_file_by_path(self.workspace_id, path)
            if existing is not None:
                raise ValueError(f"File already exists at path: {path}")

        # Auto-detect MIME type if not provided
        if mime_type is None:
            mime_type, _ = mimetypes.guess_type(filename)
            mime_type = mime_type or "application/octet-stream"

        # Compute checksum
        checksum = compute_file_checksum(content)

        # Generate unique file ID for storage
        file_id = str(uuid.uuid4())

        # Store file in storage backend
        storage = await get_workspace_storage()
        storage_path = await storage.store(
            workspace_id=self.workspace_id,
            file_id=file_id,
            filename=filename,
            content=content,
        )

        # Create database record - handle race condition where another request
        # created a file at the same path between our check and create
        async def _persist_db_record(
            retries: int = 2 if overwrite else 0,
        ) -> WorkspaceFile:
            """Create DB record, retrying on conflict if overwrite=True.

            Cleans up the orphaned storage file on any failure.
            """
            try:
                return await db.create_workspace_file(
                    workspace_id=self.workspace_id,
                    file_id=file_id,
                    name=filename,
                    path=path,
                    storage_path=storage_path,
                    mime_type=mime_type,
                    size_bytes=len(content),
                    checksum=checksum,
                    metadata=metadata,
                )
            except UniqueViolationError:
                if retries > 0:
                    # Delete conflicting file and retry
                    existing = await db.get_workspace_file_by_path(
                        self.workspace_id, path
                    )
                    if existing:
                        await self.delete_file(existing.id)
                    return await _persist_db_record(retries=retries - 1)
                if overwrite:
                    raise ValueError(
                        f"Unable to overwrite file at path: {path} "
                        f"(concurrent write conflict)"
                    ) from None
                raise ValueError(f"File already exists at path: {path}")

        try:
            file = await _persist_db_record()
        except Exception:
            try:
                await storage.delete(storage_path)
            except Exception as e:
                logger.warning(f"Failed to clean up orphaned storage file: {e}")
            raise

        logger.info(
            f"Wrote file {file.id} ({filename}) to workspace {self.workspace_id} "
            f"at path {path}, size={len(content)} bytes"
        )

        return file