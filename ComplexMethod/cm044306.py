def collect_api_router_routes(router_obj, collected_routes):
            """Recursively collect routes from _api_router instances."""
            if hasattr(router_obj, "_api_router"):
                for inner_route in router_obj._api_router.routes:  # type: ignore  # pylint: disable=W0212
                    if (
                        isinstance(inner_route, APIRoute)
                        and getattr(inner_route, "include_in_schema", True)
                        and (inner_route.path not in collected_routes)
                    ):
                        collected_routes[inner_route.path] = inner_route

            # Check if this router has sub-routers
            if hasattr(router_obj, "api_router") and hasattr(
                router_obj.api_router, "routes"
            ):
                for route in router_obj.api_router.routes:  # type: ignore
                    if not isinstance(route, APIRoute):
                        continue
                    endpoint = getattr(route, "endpoint", None)
                    if endpoint and hasattr(endpoint, "__self__"):
                        collect_api_router_routes(endpoint.__self__, collected_routes)