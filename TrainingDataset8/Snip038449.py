def _create_app(self) -> tornado.web.Application:
        """Create our tornado web app."""
        base = config.get_option("server.baseUrlPath")

        routes: List[Any] = [
            (
                make_url_path_regex(base, "stream"),
                BrowserWebSocketHandler,
                dict(runtime=self._runtime),
            ),
            (
                make_url_path_regex(base, "healthz"),
                HealthHandler,
                dict(callback=lambda: self._runtime.is_ready_for_browser_connection),
            ),
            (
                make_url_path_regex(base, "message"),
                MessageCacheHandler,
                dict(cache=self._runtime.message_cache),
            ),
            (
                make_url_path_regex(base, "st-metrics"),
                StatsRequestHandler,
                dict(stats_manager=self._runtime.stats_mgr),
            ),
            (
                make_url_path_regex(base, "st-allowed-message-origins"),
                AllowedMessageOriginsHandler,
                dict(callback=lambda: self._runtime.is_ready_for_browser_connection),
            ),
            (
                make_url_path_regex(
                    base,
                    UPLOAD_FILE_ROUTE,
                ),
                UploadFileRequestHandler,
                dict(
                    file_mgr=self._runtime.uploaded_file_mgr,
                    is_active_session=self._runtime.is_active_session,
                ),
            ),
            (
                make_url_path_regex(base, "assets/(.*)"),
                AssetsFileHandler,
                {"path": "%s/" % file_util.get_assets_dir()},
            ),
            (
                make_url_path_regex(base, f"{MEDIA_ENDPOINT}/(.*)"),
                MediaFileHandler,
                {"path": ""},
            ),
            (
                make_url_path_regex(base, "component/(.*)"),
                ComponentRequestHandler,
                dict(registry=ComponentRegistry.instance()),
            ),
        ]

        if config.get_option("server.scriptHealthCheckEnabled"):
            routes.extend(
                [
                    (
                        make_url_path_regex(base, "script-health-check"),
                        HealthHandler,
                        dict(
                            callback=lambda: self._runtime.does_script_run_without_error()
                        ),
                    )
                ]
            )

        if config.get_option("global.developmentMode"):
            LOGGER.debug("Serving static content from the Node dev server")
        else:
            static_path = file_util.get_static_dir()
            LOGGER.debug("Serving static content from %s", static_path)

            routes.extend(
                [
                    (
                        make_url_path_regex(base, "(.*)"),
                        StaticFileHandler,
                        {
                            "path": "%s/" % static_path,
                            "default_filename": "index.html",
                            "get_pages": lambda: set(
                                [
                                    page_info["page_name"]
                                    for page_info in source_util.get_pages(
                                        self.main_script_path
                                    ).values()
                                ]
                            ),
                        },
                    ),
                    (make_url_path_regex(base, trailing_slash=False), AddSlashHandler),
                ]
            )

        return tornado.web.Application(
            routes,
            cookie_secret=config.get_option("server.cookieSecret"),
            xsrf_cookies=config.get_option("server.enableXsrfProtection"),
            # Set the websocket message size. The default value is too low.
            websocket_max_message_size=get_max_message_size_bytes(),
            **TORNADO_SETTINGS,  # type: ignore[arg-type]
        )