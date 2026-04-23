def register(
        self, hass: HomeAssistant, app: web.Application, router: web.UrlDispatcher
    ) -> None:
        """Register the view with a router."""
        assert self.url is not None, "No url set for view"
        urls = [self.url, *self.extra_urls]
        routes: list[AbstractRoute] = []

        for method in ("get", "post", "delete", "put", "patch", "head", "options"):
            if not (handler := getattr(self, method, None)):
                continue

            handler = request_handler_factory(hass, self, handler)

            routes.extend(router.add_route(method, url, handler) for url in urls)

        # Use `get` because CORS middleware is not be loaded in emulated_hue
        if self.cors_allowed:
            allow_cors = app.get(KEY_ALLOW_ALL_CORS)
        else:
            allow_cors = app.get(KEY_ALLOW_CONFIGURED_CORS)

        if allow_cors:
            for route in routes:
                allow_cors(route)