async def _get_dashboard_info(
    hass: HomeAssistant, url_path: str | None
) -> dict[str, Any]:
    """Load a dashboard and return info on views."""
    if url_path == DEFAULT_DASHBOARD:
        url_path = None

    # When url_path is None, prefer "lovelace" dashboard if it exists (for YAML mode)
    # Otherwise fall back to dashboards[None] (storage mode default)
    if url_path is None:
        dashboard = hass.data[LOVELACE_DATA].dashboards.get(DOMAIN) or hass.data[
            LOVELACE_DATA
        ].dashboards.get(None)
    else:
        dashboard = hass.data[LOVELACE_DATA].dashboards.get(url_path)

    if dashboard is None:
        raise ValueError("Invalid dashboard specified")

    try:
        config = await dashboard.async_load(False)
    except ConfigNotFound:
        config = None

    if dashboard.url_path is None:
        url_path = DEFAULT_DASHBOARD
        title = "Default"
    else:
        url_path = dashboard.url_path
        title = config.get("title", url_path) if config else url_path

    views: list[dict[str, Any]] = []
    data = {
        "title": title,
        "url_path": url_path,
        "views": views,
    }

    if config is None or "views" not in config:
        return data

    for idx, view in enumerate(config["views"]):
        path = view.get("path", f"{idx}")
        views.append(
            {
                "title": view.get("title", path),
                "path": path,
            }
        )

    return data