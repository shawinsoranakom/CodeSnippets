async def _prepare_baseline_attachments(
    file_ids: list[str],
    user_id: str,
    session_id: str,
    working_dir: str,
) -> tuple[str, list[dict[str, Any]]]:
    """Download workspace files and prepare them for the baseline LLM.

    Images become OpenAI-format vision content blocks.  Non-image files are
    saved to *working_dir* so tool handlers can access them.

    Returns ``(hint_text, image_blocks)``.
    """
    if not file_ids or not user_id:
        return "", []

    try:
        manager = await get_workspace_manager(user_id, session_id)
    except Exception:
        logger.warning(
            "Failed to create workspace manager for file attachments",
            exc_info=True,
        )
        return "", []

    image_blocks: list[dict[str, Any]] = []
    file_descriptions: list[str] = []

    for fid in file_ids:
        try:
            file_info = await manager.get_file_info(fid)
            if file_info is None:
                continue
            content = await manager.read_file_by_id(fid)
            mime = (file_info.mime_type or "").split(";")[0].strip().lower()

            if mime in _VISION_MIME_TYPES and len(content) <= _MAX_INLINE_IMAGE_BYTES:
                b64 = base64.b64encode(content).decode("ascii")
                image_blocks.append(
                    {
                        "type": "image",
                        "source": {"type": "base64", "media_type": mime, "data": b64},
                    }
                )
                file_descriptions.append(
                    f"- {file_info.name} ({mime}, "
                    f"{file_info.size_bytes:,} bytes) [embedded as image]"
                )
            else:
                safe = _UNSAFE_FILENAME.sub("_", file_info.name) or "file"
                candidate = os.path.join(working_dir, safe)
                if os.path.exists(candidate):
                    stem, ext = os.path.splitext(safe)
                    idx = 1
                    while os.path.exists(candidate):
                        candidate = os.path.join(working_dir, f"{stem}_{idx}{ext}")
                        idx += 1
                with open(candidate, "wb") as f:
                    f.write(content)
                file_descriptions.append(
                    f"- {file_info.name} ({mime}, "
                    f"{file_info.size_bytes:,} bytes) saved to "
                    f"{os.path.basename(candidate)}"
                )
        except Exception:
            logger.warning("Failed to prepare file %s", fid[:12], exc_info=True)

    if not file_descriptions:
        return "", []

    noun = "file" if len(file_descriptions) == 1 else "files"
    has_non_images = len(file_descriptions) > len(image_blocks)
    read_hint = (
        " Use the read_workspace_file tool to view non-image files."
        if has_non_images
        else ""
    )
    hint = (
        f"\n[The user attached {len(file_descriptions)} {noun}.{read_hint}\n"
        + "\n".join(file_descriptions)
        + "]"
    )
    return hint, image_blocks