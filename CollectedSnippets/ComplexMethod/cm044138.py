def process_fastapi_routes_for_mcp(
    app: FastAPI, settings: MCPSettings | None = None
) -> ProcessedRouteData:
    """Single-pass processing of FastAPI routes that:

    1. Removes unwanted routes from the app in-place
    2. Builds route maps for FastMCP
    3. Creates route lookup dictionary for customization
    """
    processed = ProcessedRouteData()
    routes_to_keep = []

    for route in app.router.routes:
        if not isinstance(route, APIRoute):
            routes_to_keep.append(route)  # keep non-HTTP routes
            continue

        # Check if route should be excluded
        cfg = get_mcp_config(route)
        should_exclude = False

        # Explicit per-route exposure control
        if cfg.expose is False or _should_exclude_by_module_and_path(
            route.path or "", settings
        ):
            should_exclude = True

        if should_exclude:
            processed.removed_routes.append(route)
            continue

        # Keep the route
        routes_to_keep.append(route)

        # Build route lookup for customization (only for kept routes)
        for method in route.methods or []:
            method_upper = str(method).upper()
            if method_upper not in {"HEAD", "OPTIONS"}:
                processed.route_lookup[(route.path, method_upper)] = route

        # Build route maps for FastMCP (only for routes with explicit mcp_type)
        mcp_type_str = cfg.mcp_type.value if cfg.mcp_type else None
        mcp_type = _resolve_mcp_type(mcp_type_str)
        if mcp_type is not None:
            methods = _methods_from_config_or_route(cfg, route)
            pattern = f"^{re.escape(route.path)}$"
            if methods:
                processed.route_maps.append(
                    RouteMap(pattern=pattern, methods=methods, mcp_type=mcp_type)
                )
            else:
                processed.route_maps.append(
                    RouteMap(pattern=pattern, mcp_type=mcp_type)
                )

        # Collect prompt definitions (only for routes with prompt config)
        prompt_defs = _create_prompt_definitions_for_route(route, settings)
        if prompt_defs:
            processed.prompt_definitions.extend(prompt_defs)

    # Update the app's routes in-place
    app.router.routes = routes_to_keep

    # Add catch-all route map
    catchall_type = (
        _resolve_mcp_type(getattr(settings, "default_catchall_mcp_type", None))
        or MCPType.TOOL
    )
    processed.route_maps.append(RouteMap(pattern=r".*", mcp_type=catchall_type))

    return processed