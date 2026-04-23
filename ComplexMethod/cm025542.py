async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up WebRTC."""
    url: str | None = None
    username: str | None = None
    password: str | None = None

    if DOMAIN not in config and DEFAULT_CONFIG_DOMAIN not in config:
        await _remove_go2rtc_entries(hass)
        return True

    domain_config = config.get(DOMAIN, {})
    username = domain_config.get(CONF_USERNAME)
    password = domain_config.get(CONF_PASSWORD)

    if not (configured_by_user := DOMAIN in config) or not (
        url := domain_config.get(CONF_URL)
    ):
        if not is_docker_env():
            if not configured_by_user:
                # Remove config entry if it exists
                await _remove_go2rtc_entries(hass)
                return True
            _LOGGER.warning("Go2rtc URL required in non-docker installs")
            return False
        if not (binary := await _get_binary(hass)):
            _LOGGER.error("Could not find go2rtc docker binary")
            return False

        # Generate random credentials when not provided to secure the server
        if not username or not password:
            username = token_hex()
            password = token_hex()
            _LOGGER.debug("Generated random credentials for go2rtc server")

        auth = BasicAuth(username, password)
        # HA will manage the binary
        temp_dir = mkdtemp(prefix="go2rtc-")
        # Manually created session (not using the helper) needs to be closed manually
        # See on_stop listener below
        session = ClientSession(
            connector=UnixConnector(path=get_go2rtc_unix_socket_path(temp_dir)),
            auth=auth,
        )
        server = Server(
            hass,
            binary,
            session,
            enable_ui=domain_config.get(CONF_DEBUG_UI, False),
            username=username,
            password=password,
            working_dir=temp_dir,
        )
        try:
            await server.start()
        except Exception:  # noqa: BLE001
            _LOGGER.warning("Could not start go2rtc server", exc_info=True)
            await session.close()
            return False

        async def on_stop(event: Event) -> None:
            await server.stop()
            await session.close()

        hass.bus.async_listen(EVENT_HOMEASSISTANT_STOP, on_stop)

        url = HA_MANAGED_URL
    elif username and password:
        # Create session with BasicAuth if credentials are provided
        auth = BasicAuth(username, password)
        session = async_create_clientsession(hass, auth=auth)
    else:
        session = async_get_clientsession(hass)

    hass.data[_DATA_GO2RTC] = Go2RtcConfig(url, session)
    discovery_flow.async_create_flow(
        hass, DOMAIN, context={"source": SOURCE_SYSTEM}, data={}
    )
    return True