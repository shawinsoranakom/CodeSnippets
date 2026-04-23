async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the serving of the frontend."""
    await async_setup_frontend_storage(hass)

    panels_store = hass.data[DATA_PANELS_STORE] = Store[dict[str, dict[str, Any]]](
        hass, PANELS_STORAGE_VERSION, PANELS_STORAGE_KEY
    )
    loaded: Any = await panels_store.async_load()
    if not isinstance(loaded, dict):
        if loaded is not None:
            _LOGGER.warning("Ignoring invalid panel storage data")
        loaded = {}
    hass.data[DATA_PANELS_CONFIG] = loaded

    websocket_api.async_register_command(hass, websocket_get_icons)
    websocket_api.async_register_command(hass, websocket_get_panels)
    websocket_api.async_register_command(hass, websocket_get_themes)
    websocket_api.async_register_command(hass, websocket_get_translations)
    websocket_api.async_register_command(hass, websocket_get_version)
    websocket_api.async_register_command(hass, websocket_subscribe_extra_js)
    websocket_api.async_register_command(hass, websocket_update_panel)
    hass.http.register_view(ManifestJSONView())

    conf = config.get(DOMAIN, {})

    for key in (CONF_EXTRA_HTML_URL, CONF_EXTRA_HTML_URL_ES5, CONF_JS_VERSION):
        if key in conf:
            _LOGGER.error(
                "Please remove %s from your frontend config. It is no longer supported",
                key,
            )

    repo_path = conf.get(CONF_FRONTEND_REPO)
    dev_pr_number = conf.get(CONF_DEVELOPMENT_PR)

    pr_cache_dir = pathlib.Path(hass.config.cache_path(DOMAIN, DEV_ARTIFACTS_DIR))
    if not dev_pr_number and pr_cache_dir.exists():
        try:
            await hass.async_add_executor_job(shutil.rmtree, pr_cache_dir)
            _LOGGER.debug("Cleaned up frontend development artifacts")
        except OSError as err:
            _LOGGER.warning(
                "Could not clean up frontend development artifacts: %s", err
            )

    # Priority: development_repo > development_pr > integrated
    if repo_path and dev_pr_number:
        _LOGGER.warning(
            "Both development_repo and development_pr are specified for frontend. "
            "Using development_repo, remove development_repo to use "
            "automatic PR download"
        )
        dev_pr_number = None

    if dev_pr_number:
        github_token: str = conf[CONF_GITHUB_TOKEN]

        try:
            dev_pr_dir = await download_pr_artifact(
                hass, dev_pr_number, github_token, pr_cache_dir
            )
            repo_path = str(dev_pr_dir)
            _LOGGER.info("Using frontend from PR #%s", dev_pr_number)
        except HomeAssistantError as err:
            _LOGGER.error(
                "Failed to download PR #%s: %s, falling back to the integrated frontend",
                dev_pr_number,
                err,
            )
        except Exception:  # pylint: disable=broad-exception-caught
            _LOGGER.exception(
                "Unexpected error downloading PR #%s, "
                "falling back to the integrated frontend",
                dev_pr_number,
            )

    is_dev = repo_path is not None
    root_path = _frontend_root(repo_path)

    static_paths_configs: list[StaticPathConfig] = []

    for path, should_cache in (
        ("service_worker.js", False),
        ("sw-modern.js", False),
        ("sw-modern.js.map", False),
        ("sw-legacy.js", False),
        ("sw-legacy.js.map", False),
        ("robots.txt", False),
        ("onboarding.html", not is_dev),
        ("static", not is_dev),
        ("frontend_latest", not is_dev),
        ("frontend_es5", not is_dev),
    ):
        static_paths_configs.append(
            StaticPathConfig(f"/{path}", str(root_path / path), should_cache)
        )

    static_paths_configs.append(
        StaticPathConfig("/auth/authorize", str(root_path / "authorize.html"), False)
    )
    # https://wicg.github.io/change-password-url/
    hass.http.register_redirect(
        "/.well-known/change-password", "/profile", redirect_exc=web.HTTPFound
    )

    local = hass.config.path("www")
    if await hass.async_add_executor_job(os.path.isdir, local):
        static_paths_configs.append(StaticPathConfig("/local", local, not is_dev))

    await hass.http.async_register_static_paths(static_paths_configs)
    # Shopping list panel was replaced by todo panel in 2023.11
    hass.http.register_redirect("/shopping-list", "/todo")

    # Developer tools moved to config panel in 2026.2
    for url in (
        "/developer-tools",
        "/developer-tools/yaml",
        "/developer-tools/state",
        "/developer-tools/action",
        "/developer-tools/template",
        "/developer-tools/event",
        "/developer-tools/statistics",
        "/developer-tools/assist",
        "/developer-tools/debug",
    ):
        hass.http.register_redirect(url, f"/config{url}")

    hass.http.app.router.register_resource(IndexView(repo_path, hass))

    async_register_built_in_panel(
        hass,
        "light",
        sidebar_icon="mdi:lamps",
        sidebar_title="light",
        show_in_sidebar=False,
    )
    async_register_built_in_panel(
        hass,
        "security",
        sidebar_icon="mdi:security",
        sidebar_title="security",
        show_in_sidebar=False,
    )
    async_register_built_in_panel(
        hass,
        "climate",
        sidebar_icon="mdi:home-thermometer",
        sidebar_title="climate",
        show_in_sidebar=False,
    )
    async_register_built_in_panel(
        hass,
        "home",
        sidebar_icon="mdi:home",
        sidebar_title="home",
        show_in_sidebar=False,
    )
    async_register_built_in_panel(
        hass,
        "maintenance",
        sidebar_icon="mdi:wrench",
        sidebar_title="maintenance",
        show_in_sidebar=False,
    )

    async_register_built_in_panel(hass, "profile")
    async_register_built_in_panel(hass, "notfound")

    @callback
    def async_change_listener(
        resource_type: str,
        change_type: str,
        url: str,
    ) -> None:
        subscribers = hass.data[DATA_WS_SUBSCRIBERS]
        json_msg = {
            "change_type": change_type,
            "item": {"type": resource_type, "url": url},
        }
        for connection, msg_id in subscribers:
            connection.send_message(websocket_api.event_message(msg_id, json_msg))

    hass.data[DATA_EXTRA_MODULE_URL] = UrlManager(
        partial(async_change_listener, "module"), conf.get(CONF_EXTRA_MODULE_URL, [])
    )
    hass.data[DATA_EXTRA_JS_URL_ES5] = UrlManager(
        partial(async_change_listener, "es5"), conf.get(CONF_EXTRA_JS_URL_ES5, [])
    )
    hass.data[DATA_WS_SUBSCRIBERS] = set()

    await _async_setup_themes(hass, conf.get(CONF_THEMES))

    return True