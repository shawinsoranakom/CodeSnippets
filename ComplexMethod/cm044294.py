def get_router_dependencies(path: str) -> list:
        """Collect APIRouter dependencies for the path and its parents."""
        router = RouterLoader.from_extensions()
        segments = [
            segment
            for segment in path.split("/")
            if segment and not segment.startswith("{")
        ]
        candidate_paths = ["/"]
        current = ""
        for segment in segments:
            current = f"{current}/{segment}" if current else f"/{segment}"
            candidate_paths.append(current)

        dependencies: list = []
        seen: set = set()

        for candidate in candidate_paths:
            try:
                api_router = router.get_attr(candidate, "api_router")
            except Exception:  # pragma: no cover
                api_router = None
            if not api_router:
                continue
            for dependency in getattr(api_router, "dependencies", []) or []:
                dependency_func = getattr(dependency, "dependency", None)
                if callable(dependency_func) and dependency_func not in seen:
                    dependencies.append(dependency)
                    seen.add(dependency_func)
        return dependencies