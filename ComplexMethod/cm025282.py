def fetch_items(
    client: JellyfinClient,
    params: dict[str, Any],
) -> list[dict[str, Any]] | None:
    """Fetch items from Jellyfin server."""
    result = client.jellyfin.user_items(params=params)

    if not result or "Items" not in result or len(result["Items"]) < 1:
        return None

    items: list[dict[str, Any]] = result["Items"]

    return [
        item
        for item in items
        if not item.get("IsFolder")
        or (item.get("IsFolder") and item.get("ChildCount", 1) > 0)
    ]