def _get_route_keys(app: FastAPI) -> set[tuple[str, str]]:
    """Collect (path, method) for all routes already on the app.

    Used to build the reserved set before loading plugins so that plugin
    routes cannot overwrite or shadow existing Langflow routes.
    """
    keys: set[tuple[str, str]] = set()
    for route in app.router.routes:
        if hasattr(route, "path") and hasattr(route, "methods"):
            for method in route.methods:
                if method != "HEAD":  # often same as GET
                    keys.add((route.path, method))
        elif hasattr(route, "path") and hasattr(route, "path_regex"):
            # Mount or similar: reserve path for all methods
            keys.add((route.path, "*"))
    return keys