def _get_item_thumbnail(
    item: dict[str, Any],
    player: Player,
    entity: SqueezeBoxMediaPlayerEntity,
    item_type: str | MediaType | None,
    search_type: str,
    internal_request: bool,
    known_apps_radios: set[str],
) -> str | None:
    """Construct path to thumbnail image."""

    track_id = item.get("artwork_track_id") or (
        item.get("id")
        if item_type == "track"
        and search_type not in known_apps_radios | {"apps", "radios"}
        else None
    )

    if track_id:
        if internal_request:
            return cast(str, player.generate_image_url_from_track_id(track_id))
        if item_type is not None:
            return entity.get_browse_image_url(item_type, item["id"], track_id)

    url = None
    content_type = item_type or "unknown"

    if search_type in ["apps", "radios"]:
        url = cast(str, player.generate_image_url(item["icon"]))
    elif image_url := item.get("image_url"):
        url = image_url

    if internal_request or not url:
        return url

    synthetic_id = entity.get_synthetic_id_and_cache_url(url)
    return entity.get_browse_image_url(content_type, "synthetic", synthetic_id)