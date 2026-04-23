async def _resolve_attachments(
    hass: HomeAssistant,
    session: ChatSession,
    attachments: list[dict] | None = None,
) -> list[conversation.Attachment]:
    """Resolve attachments for a task."""
    resolved_attachments: list[conversation.Attachment] = []
    created_files: list[Path] = []

    for attachment in attachments or []:
        media_content_id = attachment["media_content_id"]

        # Special case for certain media sources
        for integration in camera, image:
            media_source_prefix = f"media-source://{integration.DOMAIN}/"
            if not media_content_id.startswith(media_source_prefix):
                continue

            # Extract entity_id from the media content ID
            entity_id = media_content_id.removeprefix(media_source_prefix)

            # Get snapshot from entity
            image_data = await integration.async_get_image(hass, entity_id)

            temp_filename = await hass.async_add_executor_job(
                _save_camera_snapshot, image_data
            )
            created_files.append(temp_filename)

            resolved_attachments.append(
                conversation.Attachment(
                    media_content_id=media_content_id,
                    mime_type=attachment.get("media_content_type")
                    or image_data.content_type,
                    path=temp_filename,
                )
            )
            break
        else:
            # Handle regular media sources
            media = await media_source.async_resolve_media(hass, media_content_id, None)
            if media.path is None:
                raise HomeAssistantError(
                    "Only local attachments are currently supported"
                )
            resolved_attachments.append(
                conversation.Attachment(
                    media_content_id=media_content_id,
                    mime_type=attachment.get("media_content_type") or media.mime_type,
                    path=media.path,
                )
            )

    if not created_files:
        return resolved_attachments

    def cleanup_files() -> None:
        """Cleanup temporary files."""
        for file in created_files:
            file.unlink(missing_ok=True)

    @callback
    def cleanup_files_callback() -> None:
        """Cleanup temporary files."""
        hass.async_add_executor_job(cleanup_files)

    session.async_on_cleanup(cleanup_files_callback)

    return resolved_attachments