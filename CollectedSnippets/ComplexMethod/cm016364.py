def add_routes(self):
        self.user_manager.add_routes(self.routes)
        self.model_file_manager.add_routes(self.routes)
        self.custom_node_manager.add_routes(self.routes, self.app, nodes.LOADED_MODULE_DIRS.items())
        self.subgraph_manager.add_routes(self.routes, nodes.LOADED_MODULE_DIRS.items())
        self.node_replace_manager.add_routes(self.routes)
        self.app.add_subapp('/internal', self.internal_routes.get_app())

        # Prefix every route with /api for easier matching for delegation.
        # This is very useful for frontend dev server, which need to forward
        # everything except serving of static files.
        # Currently both the old endpoints without prefix and new endpoints with
        # prefix are supported.
        api_routes = web.RouteTableDef()
        for route in self.routes:
            # Custom nodes might add extra static routes. Only process non-static
            # routes to add /api prefix.
            if isinstance(route, web.RouteDef):
                api_routes.route(route.method, "/api" + route.path)(route.handler, **route.kwargs)
        self.app.add_routes(api_routes)
        self.app.add_routes(self.routes)

        # Add routes from web extensions.
        for name, dir in nodes.EXTENSION_WEB_DIRS.items():
            self.app.add_routes([web.static('/extensions/' + name, dir)])

        installed_templates_version = FrontendManager.get_installed_templates_version()
        use_legacy_templates = True
        if installed_templates_version:
            try:
                use_legacy_templates = (
                    parse_version(installed_templates_version)
                    < parse_version("0.3.0")
                )
            except Exception as exc:
                logging.warning(
                    "Unable to parse templates version '%s': %s",
                    installed_templates_version,
                    exc,
                )

        if use_legacy_templates:
            workflow_templates_path = FrontendManager.legacy_templates_path()
            if workflow_templates_path:
                self.app.add_routes([
                    web.static('/templates', workflow_templates_path)
                ])
        else:
            handler = FrontendManager.template_asset_handler()
            if handler:
                self.app.router.add_get("/templates/{path:.*}", handler)

        # Serve embedded documentation from the package
        embedded_docs_path = FrontendManager.embedded_docs_path()
        if embedded_docs_path:
            self.app.add_routes([
                web.static('/docs', embedded_docs_path)
            ])

        self.app.add_routes([
            web.static('/', self.web_root),
        ])