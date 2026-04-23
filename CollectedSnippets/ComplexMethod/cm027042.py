async def root_payload(
    hass: HomeAssistant,
    coordinator: RokuDataUpdateCoordinator,
    get_browse_image_url: GetBrowseImageUrlType,
) -> BrowseMedia:
    """Return root payload for Roku."""
    device = coordinator.data

    children = [
        item_payload(
            {"title": "Apps", "type": MediaType.APPS},
            coordinator,
            get_browse_image_url,
        )
    ]

    if device.info.device_type == "tv" and len(device.channels) > 0:
        children.append(
            item_payload(
                {"title": "TV Channels", "type": MediaType.CHANNELS},
                coordinator,
                get_browse_image_url,
            )
        )

    for child in children:
        child.thumbnail = "/api/brands/integration/roku/logo.png"

    try:
        browse_item = await media_source.async_browse_media(hass, None)

        # If domain is None, it's overview of available sources
        if browse_item.domain is None:
            if browse_item.children is not None:
                children.extend(browse_item.children)
        else:
            children.append(browse_item)
    except BrowseError:
        pass

    if len(children) == 1:
        return await async_browse_media(
            hass,
            coordinator,
            get_browse_image_url,
            children[0].media_content_id,
            children[0].media_content_type,
        )

    return BrowseMedia(
        title="Roku",
        media_class=MediaClass.DIRECTORY,
        media_content_id="",
        media_content_type="root",
        can_play=False,
        can_expand=True,
        children=children,
    )