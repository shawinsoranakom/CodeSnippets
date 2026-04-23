async def _async_handle_upload(call: ServiceCall) -> ServiceResponse:
    """Generate content from text and optionally images."""
    config_entry: GooglePhotosConfigEntry = service.async_get_config_entry(
        call.hass, DOMAIN, call.data[CONF_CONFIG_ENTRY_ID]
    )

    scopes = config_entry.data["token"]["scope"].split(" ")
    if UPLOAD_SCOPE not in scopes:
        raise HomeAssistantError(
            translation_domain=DOMAIN,
            translation_key="missing_upload_permission",
            translation_placeholders={"target": DOMAIN},
        )
    coordinator = config_entry.runtime_data
    client_api = coordinator.client
    upload_tasks = []
    file_results = await call.hass.async_add_executor_job(
        _read_file_contents, call.hass, call.data[CONF_FILENAME]
    )

    album = call.data[CONF_ALBUM]
    try:
        album_id = await coordinator.get_or_create_album(album)
    except GooglePhotosApiError as err:
        raise HomeAssistantError(
            translation_domain=DOMAIN,
            translation_key="create_album_error",
            translation_placeholders={"message": str(err)},
        ) from err

    for mime_type, content in file_results:
        upload_tasks.append(client_api.upload_content(content, mime_type))
    try:
        upload_results = await asyncio.gather(*upload_tasks)
    except GooglePhotosApiError as err:
        raise HomeAssistantError(
            translation_domain=DOMAIN,
            translation_key="upload_error",
            translation_placeholders={"message": str(err)},
        ) from err
    try:
        upload_result = await client_api.create_media_items(
            [
                NewMediaItem(SimpleMediaItem(upload_token=upload_result.upload_token))
                for upload_result in upload_results
            ],
            album_id=album_id,
        )
    except GooglePhotosApiError as err:
        raise HomeAssistantError(
            translation_domain=DOMAIN,
            translation_key="api_error",
            translation_placeholders={"message": str(err)},
        ) from err
    if call.return_response:
        return {
            "media_items": [
                {"media_item_id": item_result.media_item.id}
                for item_result in upload_result.new_media_item_results
                if item_result.media_item and item_result.media_item.id
            ],
            "album_id": album_id,
        }
    return None