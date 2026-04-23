async def root_payload(
    hass: HomeAssistant,
    speaker: SonosSpeaker,
    media: SonosMedia,
    get_browse_image_url: GetBrowseImageUrlType,
) -> BrowseMedia:
    """Return root payload for Sonos."""
    children: list[BrowseMedia] = []

    if speaker.favorites:
        children.append(
            BrowseMedia(
                title="Favorites",
                media_class=MediaClass.DIRECTORY,
                media_content_id="",
                media_content_type="favorites",
                thumbnail="/api/brands/integration/sonos/logo.png",
                can_play=False,
                can_expand=True,
            )
        )

    if await hass.async_add_executor_job(
        partial(media.library.browse_by_idstring, "tracks", "", max_items=1)
    ):
        children.append(
            BrowseMedia(
                title="Music Library",
                media_class=MediaClass.DIRECTORY,
                media_content_id="",
                media_content_type="library",
                thumbnail="/api/brands/integration/sonos/logo.png",
                can_play=False,
                can_expand=True,
            )
        )

    if "plex" in hass.config.components:
        children.append(
            BrowseMedia(
                title="Plex",
                media_class=MediaClass.APP,
                media_content_id="",
                media_content_type="plex",
                thumbnail="/api/brands/integration/plex/logo.png",
                can_play=False,
                can_expand=True,
            )
        )

    if "spotify" in hass.config.components:
        result = await spotify.async_browse_media(hass, None, None)
        if result.children:
            children.extend(result.children)

    try:
        item = await media_source.async_browse_media(
            hass, None, content_filter=media_source_filter
        )
        # If domain is None, it's overview of available sources
        if item.domain is None and item.children is not None:
            children.extend(item.children)
        else:
            children.append(item)
    except BrowseError:
        pass

    if len(children) == 1:
        return await async_browse_media(
            hass,
            speaker,
            media,
            get_browse_image_url,
            children[0].media_content_id,
            children[0].media_content_type,
        )

    return BrowseMedia(
        title="Sonos",
        media_class=MediaClass.DIRECTORY,
        media_content_id="",
        media_content_type="root",
        can_play=False,
        can_expand=True,
        children=children,
    )