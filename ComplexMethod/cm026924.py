async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the HTTP API and debug interface."""
    # Late import to ensure isal is updated before
    # we import aiohttp_fast_zlib
    (await async_import_module(hass, "aiohttp_fast_zlib")).enable()

    conf: ConfData | None = config.get(DOMAIN)

    if conf is None:
        conf = cast(ConfData, HTTP_SCHEMA({}))

    if CONF_SERVER_HOST in conf and is_hassio(hass):
        issue_id = "server_host_deprecated_hassio"
        ir.async_create_issue(
            hass,
            DOMAIN,
            issue_id,
            breaks_in_ha_version="2026.6.0",
            is_fixable=False,
            severity=ir.IssueSeverity.ERROR,
            translation_key=issue_id,
        )

    server_host = conf.get(CONF_SERVER_HOST, _DEFAULT_BIND)
    server_port = conf[CONF_SERVER_PORT]
    ssl_certificate = conf.get(CONF_SSL_CERTIFICATE)
    ssl_peer_certificate = conf.get(CONF_SSL_PEER_CERTIFICATE)
    ssl_key = conf.get(CONF_SSL_KEY)
    cors_origins = conf[CONF_CORS_ORIGINS]
    use_x_forwarded_for = conf.get(CONF_USE_X_FORWARDED_FOR, False)
    use_x_frame_options = conf[CONF_USE_X_FRAME_OPTIONS]
    trusted_proxies = conf.get(CONF_TRUSTED_PROXIES) or []
    is_ban_enabled = conf[CONF_IP_BAN_ENABLED]
    login_threshold = conf[CONF_LOGIN_ATTEMPTS_THRESHOLD]
    ssl_profile = conf[CONF_SSL_PROFILE]

    source_ip_task = create_eager_task(async_get_source_ip(hass))

    supervisor_unix_socket_path: Path | None = None
    if socket_env := os.environ.get("SUPERVISOR_CORE_API_SOCKET"):
        socket_path = Path(socket_env)
        if socket_path.is_absolute():
            supervisor_unix_socket_path = socket_path
        else:
            _LOGGER.error(
                "Invalid Supervisor Unix socket path %s: path must be absolute",
                socket_env,
            )

    server = HomeAssistantHTTP(
        hass,
        server_host=server_host,
        server_port=server_port,
        ssl_certificate=ssl_certificate,
        ssl_peer_certificate=ssl_peer_certificate,
        ssl_key=ssl_key,
        trusted_proxies=trusted_proxies,
        ssl_profile=ssl_profile,
        supervisor_unix_socket_path=supervisor_unix_socket_path,
    )
    await server.async_initialize(
        cors_origins=cors_origins,
        use_x_forwarded_for=use_x_forwarded_for,
        login_threshold=login_threshold,
        is_ban_enabled=is_ban_enabled,
        use_x_frame_options=use_x_frame_options,
    )

    async def stop_server(event: Event) -> None:
        """Stop the server."""
        await server.stop()

    async def start_server(*_: Any) -> None:
        """Start the server."""
        with async_start_setup(hass, integration="http", phase=SetupPhases.SETUP):
            hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, stop_server)
            # We already checked it's not None.
            assert conf is not None
            await start_http_server_and_save_config(hass, dict(conf), server)

    async_when_setup_or_start(hass, "frontend", start_server)

    if server.supervisor_unix_socket_path is not None:

        async def start_supervisor_unix_socket(*_: Any) -> None:
            """Start the Unix socket after the Supervisor user is available."""
            if any(
                user
                for user in await hass.auth.async_get_users()
                if user.system_generated and user.name == HASSIO_USER_NAME
            ):
                await server.async_start_supervisor_unix_socket()
            else:
                _LOGGER.error("Supervisor user not found; not starting Unix socket")

        async_when_setup_or_start(hass, "hassio", start_supervisor_unix_socket)

    hass.http = server

    local_ip = await source_ip_task

    host = local_ip
    if server_host is not None:
        # Assume the first server host name provided as API host
        host = server_host[0]

    hass.config.api = ApiConfig(
        local_ip, host, server_port, ssl_certificate is not None
    )

    @callback
    def _async_check_ssl_issue(_: Event) -> None:
        if (
            ssl_certificate is not None
            and (hass.config.external_url or hass.config.internal_url) is None
        ):
            from homeassistant.components.cloud import (  # noqa: PLC0415
                CloudNotAvailable,
                async_remote_ui_url,
            )

            try:
                async_remote_ui_url(hass)
            except CloudNotAvailable:
                ir.async_create_issue(
                    hass,
                    DOMAIN,
                    "ssl_configured_without_configured_urls",
                    is_fixable=False,
                    severity=ir.IssueSeverity.ERROR,
                    translation_key="ssl_configured_without_configured_urls",
                )

    hass.bus.async_listen_once(EVENT_HOMEASSISTANT_START, _async_check_ssl_issue)

    return True