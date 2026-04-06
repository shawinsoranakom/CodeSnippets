def add_api_websocket_route(
        self,
        path: str,
        endpoint: Callable[..., Any],
        name: str | None = None,
        *,
        dependencies: Sequence[Depends] | None = None,
    ) -> None:
        self.router.add_api_websocket_route(
            path,
            endpoint,
            name=name,
            dependencies=dependencies,
        )