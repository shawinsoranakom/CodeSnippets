def get_command_coverage(
        router: Router, sep: str | None = None
    ) -> dict[str, list[str]]:
        """Get command coverage."""
        api_router = router.api_router

        mapping = ProviderInterface().map

        coverage_map: dict[Any, Any] = {}
        for route in api_router.routes:
            openapi_extra = getattr(route, "openapi_extra")
            if openapi_extra:
                model = openapi_extra.get("model", None)
                if model:
                    providers = list(mapping[model].keys())
                    if "openbb" in providers:
                        providers.remove("openbb")

                    if hasattr(route, "path"):
                        rp = route.path if sep is None else route.path.replace("/", sep)  # type: ignore
                        if route.path not in coverage_map:  # type: ignore
                            coverage_map[rp] = []
                        coverage_map[rp] = providers
        return coverage_map