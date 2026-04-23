async def _execute(
        self,
        user_id: str | None,
        session: ChatSession,
        filename: str = "",
        source_path: str | None = None,
        content: str | None = None,
        content_base64: str | None = None,
        path: str | None = None,
        mime_type: str | None = None,
        overwrite: bool = False,
        **kwargs,
    ) -> ToolResponseBase:
        session_id = session.session_id
        if not user_id:
            return ErrorResponse(
                message="Authentication required", session_id=session_id
            )

        if not filename:
            # When ALL parameters are missing, the most likely cause is
            # output token truncation: the LLM tried to inline a very large
            # file as `content`, the SDK silently truncated the tool call
            # arguments to `{}`, and we receive nothing.  Return an
            # actionable error instead of a generic "filename required".
            has_any_content = any(
                kwargs.get(k) for k in ("content", "content_base64", "source_path")
            )
            if not has_any_content:
                return ErrorResponse(
                    message=(
                        "Tool call appears truncated (no arguments received). "
                        "This happens when the content is too large for a "
                        "single tool call. Instead of passing content inline, "
                        "first write the file to the working directory using "
                        "bash_exec (e.g. cat > /home/user/file.md << 'EOF'... "
                        "EOF), then use source_path to copy it to workspace: "
                        "write_workspace_file(filename='file.md', "
                        "source_path='/home/user/file.md')"
                    ),
                    session_id=session_id,
                )
            return ErrorResponse(
                message="Please provide a filename", session_id=session_id
            )

        source_path_arg: str | None = source_path
        content_text: str | None = content
        content_b64: str | None = content_base64

        resolved = await _resolve_write_content(
            content_text,
            content_b64,
            source_path_arg,
            session_id,
        )
        if isinstance(resolved, ErrorResponse):
            return resolved
        content_bytes: bytes = resolved

        max_size = _MAX_FILE_SIZE_MB * 1024 * 1024
        if len(content_bytes) > max_size:
            return ErrorResponse(
                message=f"File too large. Maximum size is {_MAX_FILE_SIZE_MB}MB",
                session_id=session_id,
            )

        try:
            await scan_content_safe(content_bytes, filename=filename)
            manager = await get_workspace_manager(user_id, session_id)
            rec = await manager.write_file(
                content=content_bytes,
                filename=filename,
                path=path,
                mime_type=mime_type,
                overwrite=overwrite,
                metadata={"origin": "agent-created"},
            )

            # Build informative source label and message.
            if source_path_arg:
                source = f"copied from {source_path_arg}"
                msg = (
                    f"Copied {source_path_arg} → workspace:{rec.path} "
                    f"({rec.size_bytes:,} bytes)"
                )
            elif content_b64:
                source = "base64"
                msg = (
                    f"Wrote {rec.name} to workspace ({rec.size_bytes:,} bytes, "
                    f"decoded from base64)"
                )
            else:
                source = "content"
                msg = f"Wrote {rec.name} to workspace ({rec.size_bytes:,} bytes)"

            # Include a short preview for text content.
            preview: str | None = None
            if _is_text_mime(rec.mime_type):
                try:
                    preview = content_bytes[:200].decode("utf-8", errors="replace")
                    if len(content_bytes) > 200:
                        preview += "..."
                except Exception:
                    pass

            # Strip MIME parameters (e.g. "text/html; charset=utf-8" → "text/html")
            # and normalise to lowercase so the fragment is URL-safe.
            normalized_mime = (rec.mime_type or "").split(";", 1)[0].strip().lower()
            download_url = (
                f"workspace://{rec.id}#{normalized_mime}"
                if normalized_mime
                else f"workspace://{rec.id}"
            )
            return WorkspaceWriteResponse(
                file_id=rec.id,
                name=rec.name,
                path=rec.path,
                mime_type=normalized_mime,
                size_bytes=rec.size_bytes,
                download_url=download_url,
                source=source,
                content_preview=preview,
                message=msg,
                session_id=session_id,
            )
        except ValueError as e:
            return ErrorResponse(message=str(e), session_id=session_id)
        except Exception as e:
            logger.error(f"Error writing workspace file: {e}", exc_info=True)
            return ErrorResponse(
                message=f"Failed to write workspace file: {e}",
                error=str(e),
                session_id=session_id,
            )