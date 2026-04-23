async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the Hass.io component."""
    # Check local setup
    for env in ("SUPERVISOR", "SUPERVISOR_TOKEN"):
        if os.environ.get(env):
            continue
        _LOGGER.error("Missing %s environment variable", env)
        if config_entries := hass.config_entries.async_entries(DOMAIN):
            hass.async_create_task(
                hass.config_entries.async_remove(config_entries[0].entry_id)
            )
        return False

    async_load_websocket_api(hass)
    frontend.async_register_built_in_panel(hass, "app")

    host = os.environ["SUPERVISOR"]
    websession = async_get_clientsession(hass)
    hass.data[DATA_COMPONENT] = HassIO(hass.loop, websession, host)
    supervisor_client = get_supervisor_client(hass)

    try:
        await supervisor_client.supervisor.ping()
    except SupervisorError:
        _LOGGER.warning("Not connected with the supervisor / system too busy!")

    # Load the store
    config_store = HassioConfig(hass)
    await config_store.load()
    hass.data[DATA_CONFIG_STORE] = config_store

    refresh_token = None
    if (hassio_user := config_store.data.hassio_user) is not None:
        user = await hass.auth.async_get_user(hassio_user)
        if user and user.refresh_tokens:
            refresh_token = list(user.refresh_tokens.values())[0]

            # Migrate old Hass.io users to be admin.
            if not user.is_admin:
                await hass.auth.async_update_user(user, group_ids=[GROUP_ID_ADMIN])

            # Migrate old name
            if user.name == "Hass.io":
                await hass.auth.async_update_user(user, name=HASSIO_USER_NAME)

    if refresh_token is None:
        user = await hass.auth.async_create_system_user(
            HASSIO_USER_NAME, group_ids=[GROUP_ID_ADMIN]
        )
        refresh_token = await hass.auth.async_create_refresh_token(user)
        config_store.update(hassio_user=user.id)

    hass.http.register_view(HassIOView(host, websession))

    async def update_hass_api(http_config: dict[str, Any], refresh_token: RefreshToken):
        """Update Home Assistant API data on Hass.io."""
        options = HomeAssistantOptions(
            ssl=CONF_SSL_CERTIFICATE in http_config,
            port=http_config.get(CONF_SERVER_PORT) or SERVER_PORT,
            refresh_token=refresh_token.token,
        )

        if http_config.get(CONF_SERVER_HOST) is not None:
            options = replace(options, watchdog=False)
            _LOGGER.warning(
                "Found incompatible HTTP option 'server_host'. Watchdog feature"
                " disabled"
            )

        try:
            await supervisor_client.homeassistant.set_options(options)
        except SupervisorError as err:
            _LOGGER.warning(
                "Failed to update Home Assistant options in Supervisor: %s", err
            )

    update_hass_api_task = hass.async_create_task(
        update_hass_api(config.get("http", {}), refresh_token), eager_start=True
    )

    last_timezone = None
    last_country = None

    async def push_config(_: Event | None) -> None:
        """Push core config to Hass.io."""
        nonlocal last_timezone
        nonlocal last_country

        new_timezone = hass.config.time_zone
        new_country = hass.config.country

        if new_timezone != last_timezone or new_country != last_country:
            last_timezone = new_timezone
            last_country = new_country

            try:
                await supervisor_client.supervisor.set_options(
                    SupervisorOptions(timezone=new_timezone, country=new_country)
                )
            except SupervisorError as err:
                _LOGGER.warning("Failed to update Supervisor options: %s", err)

    hass.bus.async_listen(EVENT_CORE_CONFIG_UPDATE, push_config)

    push_config_task = hass.async_create_task(push_config(None), eager_start=True)
    # Start listening for problems with supervisor and making issues
    hass.data[DATA_KEY_SUPERVISOR_ISSUES] = issues = SupervisorIssues(hass)
    issues_task = hass.async_create_task(issues.setup(), eager_start=True)

    # Register services
    async_setup_services(hass, supervisor_client)

    async def update_info_data(_: datetime | None = None) -> None:
        """Update last available supervisor information."""
        supervisor_client = get_supervisor_client(hass)

        try:
            (
                root_info,
                host_info,
                store_info,
                homeassistant_info,
                supervisor_info,
                os_info,
                network_info,
                addons_list,
            ) = cast(
                tuple[
                    RootInfo,
                    HostInfo,
                    StoreInfo,
                    HomeAssistantInfo,
                    SupervisorInfo,
                    OSInfo,
                    NetworkInfo,
                    list[InstalledAddon],
                ],
                await asyncio.gather(
                    create_eager_task(supervisor_client.info()),
                    create_eager_task(supervisor_client.host.info()),
                    create_eager_task(supervisor_client.store.info()),
                    create_eager_task(supervisor_client.homeassistant.info()),
                    create_eager_task(supervisor_client.supervisor.info()),
                    create_eager_task(supervisor_client.os.info()),
                    create_eager_task(supervisor_client.network.info()),
                    create_eager_task(supervisor_client.addons.list()),
                ),
            )

        except SupervisorError as err:
            _LOGGER.warning("Can't read Supervisor data: %s", err)
        else:
            hass.data[DATA_INFO] = root_info
            hass.data[DATA_HOST_INFO] = host_info
            hass.data[DATA_STORE] = store_info
            hass.data[DATA_CORE_INFO] = homeassistant_info
            hass.data[DATA_SUPERVISOR_INFO] = supervisor_info
            hass.data[DATA_OS_INFO] = os_info
            hass.data[DATA_NETWORK_INFO] = network_info
            hass.data[DATA_ADDONS_LIST] = addons_list

    # Fetch data
    update_info_task = hass.async_create_task(update_info_data(), eager_start=True)

    async def _async_stop(hass: HomeAssistant, restart: bool) -> None:
        """Stop or restart home assistant."""
        if restart:
            await supervisor_client.homeassistant.restart()
        else:
            await supervisor_client.homeassistant.stop()

    # Set a custom handler for the homeassistant.restart and homeassistant.stop services
    async_set_stop_handler(hass, _async_stop)

    # Init discovery Hass.io feature
    async_setup_discovery_view(hass)

    # Init auth Hass.io feature
    assert user is not None
    async_setup_auth_view(hass, user)

    # Init ingress Hass.io feature
    async_setup_ingress_view(hass, host)

    # Init add-on ingress panels
    panels_task = hass.async_create_task(
        async_setup_addon_panel(hass), eager_start=True
    )

    # Make sure to await the update_info task before
    # _async_setup_hardware_integration is called
    # so the hardware integration can be set up
    # and does not fallback to calling later
    await update_hass_api_task
    await panels_task
    await update_info_task
    await push_config_task
    await issues_task

    # Setup hardware integration for the detected board type
    @callback
    def _async_setup_hardware_integration(_: datetime | None = None) -> None:
        """Set up hardware integration for the detected board type."""
        if (os_info := get_os_info(hass)) is None:
            # os info not yet fetched from supervisor, retry later
            async_call_later(
                hass,
                HASSIO_MAIN_UPDATE_INTERVAL,
                async_setup_hardware_integration_job,
            )
            return
        if (board := os_info.get("board")) is None:
            return
        if (hw_integration := HARDWARE_INTEGRATIONS.get(board)) is None:
            return
        discovery_flow.async_create_flow(
            hass, hw_integration, context={"source": SOURCE_SYSTEM}, data={}
        )

    async_setup_hardware_integration_job = HassJob(
        _async_setup_hardware_integration, cancel_on_shutdown=True
    )

    _async_setup_hardware_integration()
    discovery_flow.async_create_flow(
        hass, DOMAIN, context={"source": SOURCE_SYSTEM}, data={}
    )
    return True