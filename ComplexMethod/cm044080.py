async def get_additional_widgets(app: FastAPI) -> dict:
    """Collect widgets.json from non-root endpoints."""
    if not has_additional_widgets(app):
        return {}

    widget_routes: list[BaseRoute] = []
    for d in app.routes:
        d_path = getattr(d, "path", "")
        if d_path not in {"/widgets.json", ""} and d_path.endswith("widgets.json"):
            widget_routes.append(d)

    path_widgets: dict = {}

    for r in widget_routes:
        if (
            not getattr(r, "endpoint", None)
            or getattr(r, "path", "") == "/widgets.json"
        ):
            continue

        widgets = await r.endpoint()  # type: ignore

        if not isinstance(widgets, dict):
            continue

        path = getattr(r, "path", "")
        path_widgets[path.replace("widgets.json", "")] = dict(widgets.items())

    return path_widgets