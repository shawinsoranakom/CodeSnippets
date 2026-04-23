async def _execute(
        self,
        user_id: str | None,
        session: ChatSession,
        file_id: Optional[str] = None,
        path: Optional[str] = None,
        save_to_path: Optional[str] = None,
        force_download_url: bool = False,
        offset: int = 0,
        length: Optional[int] = None,
        **kwargs,
    ) -> ToolResponseBase:
        session_id = session.session_id
        if not user_id:
            return ErrorResponse(
                message="Authentication required", session_id=session_id
            )

        char_offset: int = max(0, offset)
        char_length: Optional[int] = length

        if not file_id and not path:
            return ErrorResponse(
                message="Please provide either file_id or path", session_id=session_id
            )

        try:
            manager = await get_workspace_manager(user_id, session_id)
            resolved = await _resolve_file(manager, file_id, path, session_id)
            if isinstance(resolved, ErrorResponse):
                # Fallback: if the path is an SDK tool-result on local disk,
                # read it directly instead of failing.  The model sometimes
                # calls read_workspace_file for these paths by mistake.
                sdk_cwd = get_sdk_cwd()
                if path and is_allowed_local_path(path, sdk_cwd):
                    return _read_local_tool_result(
                        path, char_offset, char_length, session_id, sdk_cwd=sdk_cwd
                    )
                return resolved
            target_file_id, file_info = resolved

            # If save_to_path, read + save; cache bytes for possible inline reuse.
            cached_content: bytes | None = None
            if save_to_path:
                cached_content = await manager.read_file_by_id(target_file_id)
                result = await _save_to_path(save_to_path, cached_content, session_id)
                if isinstance(result, ErrorResponse):
                    return result
                save_to_path = result

            # Ranged read: return a character slice directly.
            if char_offset > 0 or char_length is not None:
                raw = cached_content or await manager.read_file_by_id(target_file_id)
                text = raw.decode("utf-8", errors="replace")
                total_chars = len(text)
                end = (
                    char_offset + char_length
                    if char_length is not None
                    else total_chars
                )
                slice_text = text[char_offset:end]
                return WorkspaceFileContentResponse(
                    file_id=file_info.id,
                    name=file_info.name,
                    path=file_info.path,
                    mime_type="text/plain",
                    content_base64=base64.b64encode(slice_text.encode("utf-8")).decode(
                        "utf-8"
                    ),
                    message=(
                        f"Read chars {char_offset}–"
                        f"{char_offset + len(slice_text)} "
                        f"of {total_chars:,} total "
                        f"from {file_info.name}"
                    ),
                    session_id=session_id,
                )

            is_small = file_info.size_bytes <= self.MAX_INLINE_SIZE_BYTES
            is_text = _is_text_mime(file_info.mime_type)
            is_image = file_info.mime_type in _IMAGE_MIME_TYPES

            # Inline content for small text/image files
            if is_small and (is_text or is_image) and not force_download_url:
                content = cached_content or await manager.read_file_by_id(
                    target_file_id
                )
                msg = (
                    f"Read {file_info.name} from workspace:{file_info.path} "
                    f"({file_info.size_bytes:,} bytes, {file_info.mime_type})"
                )
                if save_to_path:
                    msg += f" — also saved to {save_to_path}"
                return WorkspaceFileContentResponse(
                    file_id=file_info.id,
                    name=file_info.name,
                    path=file_info.path,
                    mime_type=file_info.mime_type,
                    content_base64=base64.b64encode(content).decode("utf-8"),
                    message=msg,
                    session_id=session_id,
                )

            # Metadata + download URL for large/binary files
            preview: str | None = None
            if is_text:
                try:
                    raw = cached_content or await manager.read_file_by_id(
                        target_file_id
                    )
                    preview = raw[: self.PREVIEW_SIZE].decode("utf-8", errors="replace")
                    if len(raw) > self.PREVIEW_SIZE:
                        preview += "..."
                except Exception:
                    pass

            msg = (
                f"File: {file_info.name} at workspace:{file_info.path} "
                f"({file_info.size_bytes:,} bytes, {file_info.mime_type})"
            )
            if save_to_path:
                msg += f" — saved to {save_to_path}"
            else:
                msg += (
                    " — use read_workspace_file with this file_id to retrieve content"
                )
            return WorkspaceFileMetadataResponse(
                file_id=file_info.id,
                name=file_info.name,
                path=file_info.path,
                mime_type=file_info.mime_type,
                size_bytes=file_info.size_bytes,
                download_url=f"workspace://{target_file_id}",
                preview=preview,
                message=msg,
                session_id=session_id,
            )
        except FileNotFoundError as e:
            return ErrorResponse(message=str(e), session_id=session_id)
        except Exception as e:
            logger.error(f"Error reading workspace file: {e}", exc_info=True)
            return ErrorResponse(
                message=f"Failed to read workspace file: {e}",
                error=str(e),
                session_id=session_id,
            )