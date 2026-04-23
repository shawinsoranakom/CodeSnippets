async def async_generate_image(
    hass: HomeAssistant,
    *,
    task_name: str,
    entity_id: str | None = None,
    instructions: str,
    attachments: list[dict] | None = None,
) -> ServiceResponse:
    """Run an image generation task in the AI Task integration."""
    if entity_id is None:
        entity_id = hass.data[DATA_PREFERENCES].gen_image_entity_id

    if entity_id is None:
        raise HomeAssistantError("No entity_id provided and no preferred entity set")

    entity = hass.data[DATA_COMPONENT].get_entity(entity_id)
    if entity is None:
        raise HomeAssistantError(f"AI Task entity {entity_id} not found")

    if AITaskEntityFeature.GENERATE_IMAGE not in entity.supported_features:
        raise HomeAssistantError(
            f"AI Task entity {entity_id} does not support generating images"
        )

    if (
        attachments
        and AITaskEntityFeature.SUPPORT_ATTACHMENTS not in entity.supported_features
    ):
        raise HomeAssistantError(
            f"AI Task entity {entity_id} does not support attachments"
        )

    with async_get_chat_session(hass) as session:
        resolved_attachments = await _resolve_attachments(hass, session, attachments)

        task_result = await entity.internal_async_generate_image(
            session,
            GenImageTask(
                name=task_name,
                instructions=instructions,
                attachments=resolved_attachments or None,
            ),
        )

    service_result = task_result.as_dict()
    image_data = service_result.pop("image_data")
    if service_result.get("revised_prompt") is None:
        service_result["revised_prompt"] = instructions

    source = hass.data[DATA_MEDIA_SOURCE]

    current_time = datetime.now()
    ext = mimetypes.guess_extension(task_result.mime_type, False) or ".png"
    sanitized_task_name = RE_SANITIZE_FILENAME.sub("", slugify(task_name))

    image_file = ImageData(
        filename=f"{current_time.strftime('%Y-%m-%d_%H%M%S')}_{sanitized_task_name}{ext}",
        file=io.BytesIO(image_data),
        content_type=task_result.mime_type,
    )

    target_folder = media_source.MediaSourceItem.from_uri(
        hass, f"media-source://{DOMAIN}/{IMAGE_DIR}", None
    )

    service_result["media_source_id"] = await source.async_upload_media(
        target_folder, image_file
    )

    item = media_source.MediaSourceItem.from_uri(
        hass, service_result["media_source_id"], None
    )
    service_result["url"] = async_sign_path(
        hass,
        (await source.async_resolve_media(item)).url,
        timedelta(seconds=IMAGE_EXPIRY_TIME),
    )

    return service_result