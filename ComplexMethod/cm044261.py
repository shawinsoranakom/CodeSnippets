def get_provider_coverage(
        router: Router, sep: str | None = None
    ) -> dict[str, list[str]]:
        """Get provider coverage."""
        api_router = router.api_router

        mapping = ProviderInterface().map

        coverage_map: dict[Any, Any] = {}
        for route in api_router.routes:
            openapi_extra = getattr(route, "openapi_extra", None)
            if openapi_extra:
                model = openapi_extra.get("model", None)
                if model:
                    providers = list(mapping[model].keys())
                    if "openbb" in providers:
                        providers.remove("openbb")
                    for provider in providers:
                        if provider not in coverage_map:
                            coverage_map[provider] = []
                        if hasattr(route, "path"):
                            rp = (
                                route.path  # type: ignore
                                if sep is None
                                else route.path.replace("/", sep)  # type: ignore
                            )
                            coverage_map[provider].append(rp)

        return coverage_map