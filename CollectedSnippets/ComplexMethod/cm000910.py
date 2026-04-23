async def _prepare_file_attachments(
    file_ids: list[str],
    user_id: str,
    session_id: str,
    sdk_cwd: str,
) -> PreparedAttachments:
    """Download workspace files and prepare them for Claude.

    Images (PNG/JPEG/GIF/WebP) are embedded directly as vision content blocks
    in the user message so Claude can see them without tool calls.

    Non-image files (PDFs, text, etc.) are saved to *sdk_cwd* so the CLI's
    built-in Read tool can access them.

    Returns a :class:`PreparedAttachments` with a text hint and any image
    content blocks.
    """
    empty = PreparedAttachments(hint="", image_blocks=[])
    if not file_ids or not user_id:
        return empty

    try:
        manager = await get_workspace_manager(user_id, session_id)
    except Exception:
        logger.warning(
            "Failed to create workspace manager for file attachments",
            exc_info=True,
        )
        return empty

    image_blocks: list[dict[str, Any]] = []
    file_descriptions: list[str] = []

    for fid in file_ids:
        try:
            file_info = await manager.get_file_info(fid)
            if file_info is None:
                continue
            content = await manager.read_file_by_id(fid)
            mime = (file_info.mime_type or "").split(";")[0].strip().lower()

            # Images: embed directly in the user message as vision blocks
            if mime in _VISION_MIME_TYPES and len(content) <= _MAX_INLINE_IMAGE_BYTES:
                b64 = base64.b64encode(content).decode("ascii")
                image_blocks.append(
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": mime,
                            "data": b64,
                        },
                    }
                )
                file_descriptions.append(
                    f"- {file_info.name} ({mime}, "
                    f"{file_info.size_bytes:,} bytes) [embedded as image]"
                )
            else:
                # Non-image files: save to sdk_cwd for Read tool access
                local_path = _save_to_sdk_cwd(sdk_cwd, file_info.name, content)
                file_descriptions.append(
                    f"- {file_info.name} ({mime}, "
                    f"{file_info.size_bytes:,} bytes) saved to {local_path}"
                )
        except Exception:
            logger.warning("Failed to prepare file %s", fid[:12], exc_info=True)

    if not file_descriptions:
        return empty

    noun = "file" if len(file_descriptions) == 1 else "files"
    has_non_images = len(file_descriptions) > len(image_blocks)
    read_hint = " Use the Read tool to view non-image files." if has_non_images else ""
    hint = (
        f"[The user attached {len(file_descriptions)} {noun}.{read_hint}\n"
        + "\n".join(file_descriptions)
        + "]"
    )
    return PreparedAttachments(hint=hint, image_blocks=image_blocks)