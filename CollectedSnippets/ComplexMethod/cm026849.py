async def async_browse_media(
    hass: HomeAssistant,
    media_content_type: MediaType | str,
    media_content_id: str,
    cast_type: str,
) -> BrowseMedia | None:
    """Browse media."""
    if media_content_type != DOMAIN:
        return None

    try:
        get_url(hass, require_ssl=True, prefer_external=True)
    except NoURLAvailableError as err:
        raise BrowseError(NO_URL_AVAILABLE_ERROR) from err

    # List dashboards.
    if not media_content_id:
        children = [
            BrowseMedia(
                title="Default",
                media_class=MediaClass.APP,
                media_content_id=DEFAULT_DASHBOARD,
                media_content_type=DOMAIN,
                thumbnail="/api/brands/integration/lovelace/logo.png",
                can_play=True,
                can_expand=False,
            )
        ]
        for url_path in hass.data[LOVELACE_DATA].dashboards:
            if url_path is None:
                continue

            info = await _get_dashboard_info(hass, url_path)
            children.append(_item_from_info(info))

        root = (await async_get_media_browser_root_object(hass, CAST_TYPE_CHROMECAST))[
            0
        ]
        root.children = children
        return root

    try:
        info = await _get_dashboard_info(hass, media_content_id)
    except ValueError as err:
        raise BrowseError(f"Dashboard {media_content_id} not found") from err

    children = []

    for view in info["views"]:
        children.append(
            BrowseMedia(
                title=view["title"],
                media_class=MediaClass.APP,
                media_content_id=f"{info['url_path']}/{view['path']}",
                media_content_type=DOMAIN,
                thumbnail="/api/brands/integration/lovelace/logo.png",
                can_play=True,
                can_expand=False,
            )
        )

    root = _item_from_info(info)
    root.children = children
    return root