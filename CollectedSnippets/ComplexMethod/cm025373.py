async def async_browse_media(
    hass: HomeAssistant,
    speaker: SonosSpeaker,
    media: SonosMedia,
    get_browse_image_url: GetBrowseImageUrlType,
    media_content_id: str | None,
    media_content_type: str | None,
) -> BrowseMedia:
    """Browse media."""

    if media_content_id is None:
        return await root_payload(
            hass,
            speaker,
            media,
            get_browse_image_url,
        )
    assert media_content_type is not None

    if media_source.is_media_source_id(media_content_id):
        return await media_source.async_browse_media(
            hass, media_content_id, content_filter=media_source_filter
        )

    if plex.is_plex_media_id(media_content_id):
        return await plex.async_browse_media(
            hass, media_content_type, media_content_id, platform=DOMAIN
        )

    if media_content_type == "plex":
        return await plex.async_browse_media(hass, None, None, platform=DOMAIN)

    if spotify.is_spotify_media_type(media_content_type):
        return await spotify.async_browse_media(
            hass, media_content_type, media_content_id, can_play_artist=False
        )

    if media_content_type == "library":
        return await hass.async_add_executor_job(
            library_payload,
            media.library,
            partial(
                get_thumbnail_url_full,
                media,
                is_internal_request(hass),
                get_browse_image_url,
            ),
        )

    if media_content_type == "favorites":
        return await hass.async_add_executor_job(
            favorites_payload,
            speaker.favorites,
        )

    if media_content_type == "favorites_folder":
        return await hass.async_add_executor_job(
            favorites_folder_payload,
            speaker.favorites,
            media_content_id,
            media,
            get_browse_image_url,
        )

    payload = {
        "search_type": media_content_type,
        "idstring": media_content_id,
    }
    response = await hass.async_add_executor_job(
        build_item_response,
        media.library,
        payload,
        partial(
            get_thumbnail_url_full,
            media,
            is_internal_request(hass),
            get_browse_image_url,
        ),
    )
    if response is None:
        raise BrowseError(f"Media not found: {media_content_type} / {media_content_id}")
    return response