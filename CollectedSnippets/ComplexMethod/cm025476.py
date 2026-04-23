async def async_browse_media(
    hass: HomeAssistant,
    media_content_id: str | None,
    *,
    content_filter: Callable[[BrowseMedia], bool] | None = None,
) -> BrowseMediaSource:
    """Return media player browse media results."""
    if DOMAIN not in hass.data:
        raise BrowseError("Media Source not loaded")

    try:
        item = await _get_media_item(hass, media_content_id, None).async_browse()
    except ValueError as err:
        raise BrowseError(
            translation_domain=DOMAIN,
            translation_key="browse_media_failed",
            translation_placeholders={
                "media_content_id": str(media_content_id),
                "error": str(err),
            },
        ) from err

    if content_filter is None or item.children is None:
        return item

    old_count = len(item.children)
    item.children = [
        child for child in item.children if child.can_expand or content_filter(child)
    ]
    item.not_shown += old_count - len(item.children)
    return item