async def async_setup_entry(  # noqa: C901
    hass: HomeAssistant, entry: RainMachineConfigEntry
) -> bool:
    """Set up RainMachine as config entry."""
    websession = aiohttp_client.async_get_clientsession(hass)
    client = Client(session=websession)
    ip_address = entry.data[CONF_IP_ADDRESS]

    try:
        await client.load_local(
            ip_address,
            entry.data[CONF_PASSWORD],
            port=entry.data[CONF_PORT],
            use_ssl=entry.data.get(CONF_SSL, DEFAULT_SSL),
        )
    except RainMachineError as err:
        raise ConfigEntryNotReady from err

    # regenmaschine can load multiple controllers at once, but we only grab the one
    # we loaded above:
    controller = get_client_controller(client)

    entry_updates: dict[str, Any] = {}
    if not entry.unique_id or is_ip_address(entry.unique_id):
        # If the config entry doesn't already have a unique ID, set one:
        entry_updates["unique_id"] = controller.mac

    if CONF_DEFAULT_ZONE_RUN_TIME in entry.data:
        # If a zone run time exists in the config entry's data, pop it and move it to
        # options:
        data = {**entry.data}
        entry_updates["data"] = data
        entry_updates["options"] = {
            **entry.options,
            CONF_DEFAULT_ZONE_RUN_TIME: data.pop(CONF_DEFAULT_ZONE_RUN_TIME),
        }
    entry_updates["options"] = {**entry.options}
    if CONF_USE_APP_RUN_TIMES not in entry.options:
        entry_updates["options"][CONF_USE_APP_RUN_TIMES] = False
    if CONF_DEFAULT_ZONE_RUN_TIME not in entry.options:
        entry_updates["options"][CONF_DEFAULT_ZONE_RUN_TIME] = DEFAULT_ZONE_RUN
    if CONF_ALLOW_INACTIVE_ZONES_TO_RUN not in entry.options:
        entry_updates["options"][CONF_ALLOW_INACTIVE_ZONES_TO_RUN] = False
    if entry_updates:
        hass.config_entries.async_update_entry(entry, **entry_updates)

    if entry.unique_id and controller.mac != entry.unique_id:
        # If the mac address of the device does not match the unique_id
        # of the config entry, it likely means the DHCP lease has expired
        # and the device has been assigned a new IP address. We need to
        # wait for the next discovery to find the device at its new address
        # and update the config entry so we do not mix up devices.
        raise ConfigEntryNotReady(
            f"Unexpected device found at {ip_address}; expected {entry.unique_id}, "
            f"found {controller.mac}"
        )

    async def async_update(api_category: str) -> dict:
        """Update the appropriate API data based on a category."""
        data: dict = {}

        try:
            if api_category == DATA_API_VERSIONS:
                data = await controller.api.versions()
            elif api_category == DATA_MACHINE_FIRMWARE_UPDATE_STATUS:
                data = await controller.machine.get_firmware_update_status()
            elif api_category == DATA_PROGRAMS:
                data = await controller.programs.all(include_inactive=True)
            elif api_category == DATA_PROVISION_SETTINGS:
                data = await controller.provisioning.settings()
            elif api_category == DATA_RESTRICTIONS_CURRENT:
                data = await controller.restrictions.current()
            elif api_category == DATA_RESTRICTIONS_UNIVERSAL:
                data = await controller.restrictions.universal()
            else:
                data = await controller.zones.all(details=True, include_inactive=True)
        except UnknownAPICallError:
            LOGGER.warning(
                "Skipping unsupported API call for controller %s: %s",
                controller.name,
                api_category,
            )
        except RainMachineError as err:
            raise UpdateFailed(err) from err

        return data

    coordinators = {}
    for api_category, update_interval in COORDINATOR_UPDATE_INTERVAL_MAP.items():
        coordinator = coordinators[api_category] = RainMachineDataUpdateCoordinator(
            hass,
            entry=entry,
            name=f'{controller.name} ("{api_category}")',
            api_category=api_category,
            update_interval=update_interval,
            update_method=partial(async_update, api_category),
        )
        coordinator.async_initialize()
        # Its generally faster not to gather here so we can
        # reuse the connection instead of creating a new
        # connection for each coordinator.
        await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = RainMachineData(
        controller=controller, coordinators=coordinators
    )

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    def call_with_controller(
        update_programs_and_zones: bool = True,
    ) -> Callable[
        [Callable[[ServiceCall, Controller], Coroutine[Any, Any, None]]],
        Callable[[ServiceCall], Coroutine[Any, Any, None]],
    ]:
        """Hydrate a service call with the appropriate controller."""

        def decorator(
            func: Callable[[ServiceCall, Controller], Coroutine[Any, Any, None]],
        ) -> Callable[[ServiceCall], Coroutine[Any, Any, None]]:
            """Define the decorator."""

            @wraps(func)
            async def wrapper(call: ServiceCall) -> None:
                """Wrap the service function."""
                entry = async_get_entry_for_service_call(hass, call)
                data = entry.runtime_data

                try:
                    await func(call, data.controller)
                except RainMachineError as err:
                    raise HomeAssistantError(
                        f"Error while executing {func.__name__}: {err}"
                    ) from err

                if update_programs_and_zones:
                    await async_update_programs_and_zones(hass, entry)

            return wrapper

        return decorator

    @call_with_controller()
    async def async_pause_watering(call: ServiceCall, controller: Controller) -> None:
        """Pause watering for a set number of seconds."""
        await controller.watering.pause_all(call.data[CONF_SECONDS])

    @call_with_controller(update_programs_and_zones=False)
    async def async_push_flow_meter_data(
        call: ServiceCall, controller: Controller
    ) -> None:
        """Push flow meter data to the device."""
        value = call.data[CONF_VALUE]
        if units := call.data.get(CONF_UNIT_OF_MEASUREMENT):
            await controller.watering.post_flowmeter(value=value, units=units)
        else:
            await controller.watering.post_flowmeter(value=value)

    @call_with_controller(update_programs_and_zones=False)
    async def async_push_weather_data(
        call: ServiceCall, controller: Controller
    ) -> None:
        """Push weather data to the device."""
        await controller.parsers.post_data(
            {
                CONF_WEATHER: [
                    {
                        key: value
                        for key, value in call.data.items()
                        if key != CONF_DEVICE_ID
                    }
                ]
            }
        )

    @call_with_controller()
    async def async_restrict_watering(
        call: ServiceCall, controller: Controller
    ) -> None:
        """Restrict watering for a time period."""
        duration = call.data[CONF_DURATION]
        await controller.restrictions.set_universal(
            {
                "rainDelayStartTime": round(as_timestamp(utcnow())),
                "rainDelayDuration": duration.total_seconds(),
            },
        )

    @call_with_controller()
    async def async_stop_all(call: ServiceCall, controller: Controller) -> None:
        """Stop all watering."""
        await controller.watering.stop_all()

    @call_with_controller()
    async def async_unpause_watering(call: ServiceCall, controller: Controller) -> None:
        """Unpause watering."""
        await controller.watering.unpause_all()

    @call_with_controller()
    async def async_unrestrict_watering(
        call: ServiceCall, controller: Controller
    ) -> None:
        """Unrestrict watering."""
        await controller.restrictions.set_universal(
            {
                "rainDelayStartTime": round(as_timestamp(utcnow())),
                "rainDelayDuration": 0,
            },
        )

    for service_name, schema, method in (
        (
            SERVICE_NAME_PAUSE_WATERING,
            SERVICE_PAUSE_WATERING_SCHEMA,
            async_pause_watering,
        ),
        (
            SERVICE_NAME_PUSH_FLOW_METER_DATA,
            SERVICE_PUSH_FLOW_METER_DATA_SCHEMA,
            async_push_flow_meter_data,
        ),
        (
            SERVICE_NAME_PUSH_WEATHER_DATA,
            SERVICE_PUSH_WEATHER_DATA_SCHEMA,
            async_push_weather_data,
        ),
        (
            SERVICE_NAME_RESTRICT_WATERING,
            SERVICE_RESTRICT_WATERING_SCHEMA,
            async_restrict_watering,
        ),
        (SERVICE_NAME_STOP_ALL, SERVICE_SCHEMA, async_stop_all),
        (SERVICE_NAME_UNPAUSE_WATERING, SERVICE_SCHEMA, async_unpause_watering),
        (
            SERVICE_NAME_UNRESTRICT_WATERING,
            SERVICE_SCHEMA,
            async_unrestrict_watering,
        ),
    ):
        if hass.services.has_service(DOMAIN, service_name):
            continue
        hass.services.async_register(
            DOMAIN,
            service_name,
            method,
            schema=schema,
            description_placeholders={
                "api_url": API_URL_REFERENCE,
            },
        )

    return True