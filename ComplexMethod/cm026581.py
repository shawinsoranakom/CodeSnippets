async def async_setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    async_add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Set up the SAJ sensors."""

    remove_interval_update = None
    wifi = config[CONF_TYPE] == INVERTER_TYPES[1]

    # Init all sensors
    sensor_def = pysaj.Sensors(wifi)

    # Use all sensors by default
    hass_sensors: list[SAJsensor] = []

    kwargs = {}
    if wifi:
        kwargs["wifi"] = True
        if config.get(CONF_USERNAME) and config.get(CONF_PASSWORD):
            kwargs["username"] = config[CONF_USERNAME]
            kwargs["password"] = config[CONF_PASSWORD]

    try:
        saj = pysaj.SAJ(config[CONF_HOST], **kwargs)
        done = await saj.read(sensor_def)
    except pysaj.UnauthorizedException:
        _LOGGER.error("Username and/or password is wrong")
        return
    except pysaj.UnexpectedResponseException as err:
        _LOGGER.error(
            "Error in SAJ, please check host/ip address. Original error: %s", err
        )
        return

    if not done:
        raise PlatformNotReady

    hass_sensors.extend(
        SAJsensor(saj.serialnumber, sensor, inverter_name=config.get(CONF_NAME))
        for sensor in sensor_def
        if sensor.enabled
    )

    async_add_entities(hass_sensors)

    async def async_saj() -> bool:
        """Update all the SAJ sensors."""
        success = await saj.read(sensor_def)

        for sensor in hass_sensors:
            state_unknown = False
            # SAJ inverters are powered by DC via solar panels and thus are
            # offline after the sun has set. If a sensor resets on a daily
            # basis like "today_yield", this reset won't happen automatically.
            # Code below checks if today > day when sensor was last updated
            # and if so: set state to None.
            # Sensors with live values like "temperature" or "current_power"
            # will also be reset to None.
            if not success and (
                (sensor.per_day_basis and date.today() > sensor.date_updated)
                or (not sensor.per_day_basis and not sensor.per_total_basis)
            ):
                state_unknown = True
            sensor.async_update_values(unknown_state=state_unknown)

        return success

    @callback
    def start_update_interval(hass: HomeAssistant) -> None:
        """Start the update interval scheduling."""
        nonlocal remove_interval_update
        remove_interval_update = async_track_time_interval_backoff(hass, async_saj)

    @callback
    def stop_update_interval(event):
        """Properly cancel the scheduled update."""
        remove_interval_update()

    hass.bus.async_listen(EVENT_HOMEASSISTANT_STOP, stop_update_interval)
    async_at_start(hass, start_update_interval)