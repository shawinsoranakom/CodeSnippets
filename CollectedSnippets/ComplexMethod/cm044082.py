async def get_additional_apps(app: FastAPI) -> dict:
    """Collect apps.json from non-root endpoints."""
    if not has_additional_apps(app):
        return {}

    apps_routes: list[BaseRoute] = []
    for d in app.routes:
        d_path = getattr(d, "path", "")
        if d_path not in {"/apps.json", ""} and d_path.endswith("apps.json"):
            apps_routes.append(d)

    path_apps: dict = {}

    for r in apps_routes:
        if not getattr(r, "endpoint", None) or getattr(r, "path", "") == "/apps.json":
            continue

        apps = await r.endpoint()  # type: ignore

        if not isinstance(apps, list):
            continue

        path = getattr(r, "path", "")
        path_apps[path.replace("apps.json", "")] = apps

    return path_apps