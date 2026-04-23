def build_item_response(
    coordinator: RokuDataUpdateCoordinator,
    payload: dict,
    get_browse_image_url: GetBrowseImageUrlType,
) -> BrowseMedia | None:
    """Create response payload for the provided media query."""
    search_id = payload["search_id"]
    search_type = payload["search_type"]

    thumbnail = None
    title = None
    media = None
    children_media_class = None

    if search_type == MediaType.APPS:
        title = "Apps"
        media = [
            {"app_id": item.app_id, "title": item.name, "type": MediaType.APP}
            for item in coordinator.data.apps
        ]
        children_media_class = MediaClass.APP
    elif search_type == MediaType.CHANNELS:
        title = "TV Channels"
        media = [
            {
                "channel_number": channel.number,
                "title": format_channel_name(channel.number, channel.name),
                "type": MediaType.CHANNEL,
            }
            for channel in coordinator.data.channels
        ]
        children_media_class = MediaClass.CHANNEL

    if title is None or media is None:
        return None

    return BrowseMedia(
        media_class=CONTAINER_TYPES_SPECIFIC_MEDIA_CLASS.get(
            search_type, MediaClass.DIRECTORY
        ),
        media_content_id=search_id,
        media_content_type=search_type,
        title=title,
        can_play=search_type in PLAYABLE_MEDIA_TYPES and search_id,
        can_expand=True,
        children=[
            item_payload(item, coordinator, get_browse_image_url) for item in media
        ],
        children_media_class=children_media_class,
        thumbnail=thumbnail,
    )