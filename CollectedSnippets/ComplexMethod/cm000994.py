async def _execute(
        self,
        user_id: str | None,
        session: ChatSession,
        path_prefix: Optional[str] = None,
        limit: int = 50,
        include_all_sessions: bool = False,
        **kwargs,
    ) -> ToolResponseBase:
        session_id = session.session_id
        if not user_id:
            return ErrorResponse(
                message="Authentication required", session_id=session_id
            )

        limit = min(limit, 100)

        try:
            manager = await get_workspace_manager(user_id, session_id)
            files = await manager.list_files(
                path=path_prefix, limit=limit, include_all_sessions=include_all_sessions
            )
            total = await manager.get_file_count(
                path=path_prefix, include_all_sessions=include_all_sessions
            )
            file_infos = [
                WorkspaceFileInfoData(
                    file_id=f.id,
                    name=f.name,
                    path=f.path,
                    mime_type=f.mime_type,
                    size_bytes=f.size_bytes,
                )
                for f in files
            ]
            scope = "all sessions" if include_all_sessions else "current session"
            total_size = sum(f.size_bytes for f in file_infos)

            # Build a human-readable summary so the agent can relay details.
            lines = [f"Found {len(files)} file(s) in workspace ({scope}):"]
            for f in file_infos:
                lines.append(f"  - {f.path} ({f.size_bytes:,} bytes, {f.mime_type})")
            if total > len(files):
                lines.append(f"  ... and {total - len(files)} more")
            lines.append(f"Total size: {total_size:,} bytes")

            return WorkspaceFileListResponse(
                files=file_infos,
                total_count=total,
                message="\n".join(lines),
                session_id=session_id,
            )
        except Exception as e:
            logger.error(f"Error listing workspace files: {e}", exc_info=True)
            return ErrorResponse(
                message=f"Failed to list workspace files: {e}",
                error=str(e),
                session_id=session_id,
            )