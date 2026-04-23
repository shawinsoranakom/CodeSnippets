async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the Amcrest IP Camera component."""
    hass.data.setdefault(DATA_AMCREST, {DEVICES: {}, CAMERAS: []})

    for device in config[DOMAIN]:
        name: str = device[CONF_NAME]
        username: str = device[CONF_USERNAME]
        password: str = device[CONF_PASSWORD]

        api = AmcrestChecker(
            hass, name, device[CONF_HOST], device[CONF_PORT], username, password
        )

        ffmpeg_arguments = device[CONF_FFMPEG_ARGUMENTS]
        resolution = RESOLUTION_LIST[device[CONF_RESOLUTION]]
        binary_sensors = device.get(CONF_BINARY_SENSORS)
        sensors = device.get(CONF_SENSORS)
        switches = device.get(CONF_SWITCHES)
        stream_source = device[CONF_STREAM_SOURCE]
        control_light = device.get(CONF_CONTROL_LIGHT)

        # currently aiohttp only works with basic authentication
        # only valid for mjpeg streaming
        if device[CONF_AUTHENTICATION] == HTTP_BASIC_AUTHENTICATION:
            authentication: aiohttp.BasicAuth | None = aiohttp.BasicAuth(
                username, password
            )
        else:
            authentication = None

        hass.data[DATA_AMCREST][DEVICES][name] = AmcrestDevice(
            api,
            authentication,
            ffmpeg_arguments,
            stream_source,
            resolution,
            control_light,
        )

        hass.async_create_task(
            discovery.async_load_platform(
                hass, Platform.CAMERA, DOMAIN, {CONF_NAME: name}, config
            )
        )

        event_codes = set()
        if binary_sensors:
            hass.async_create_task(
                discovery.async_load_platform(
                    hass,
                    Platform.BINARY_SENSOR,
                    DOMAIN,
                    {CONF_NAME: name, CONF_BINARY_SENSORS: binary_sensors},
                    config,
                )
            )
            event_codes = {
                event_code
                for sensor in BINARY_SENSORS
                if sensor.key in binary_sensors
                and not sensor.should_poll
                and sensor.event_codes is not None
                for event_code in sensor.event_codes
            }

        _start_event_monitor(hass, name, api, event_codes)

        if sensors:
            hass.async_create_task(
                discovery.async_load_platform(
                    hass,
                    Platform.SENSOR,
                    DOMAIN,
                    {CONF_NAME: name, CONF_SENSORS: sensors},
                    config,
                )
            )

        if switches:
            hass.async_create_task(
                discovery.async_load_platform(
                    hass,
                    Platform.SWITCH,
                    DOMAIN,
                    {CONF_NAME: name, CONF_SWITCHES: switches},
                    config,
                )
            )

    if not hass.data[DATA_AMCREST][DEVICES]:
        return False

    async_setup_services(hass)

    return True