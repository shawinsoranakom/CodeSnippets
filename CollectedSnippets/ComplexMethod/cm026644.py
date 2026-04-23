def setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the Tellstick component."""

    conf = config.get(DOMAIN, {})
    net_host = conf.get(CONF_HOST)
    net_ports = conf.get(CONF_PORT)

    # Initialize remote tellcore client
    if net_host:
        net_client = TellCoreClient(
            host=net_host, port_client=net_ports[0], port_events=net_ports[1]
        )
        net_client.start()

        def stop_tellcore_net(event):
            """Event handler to stop the client."""
            net_client.stop()

        hass.bus.listen_once(EVENT_HOMEASSISTANT_STOP, stop_tellcore_net)

    try:
        tellcore_lib = TelldusCore(
            callback_dispatcher=AsyncioCallbackDispatcher(hass.loop)
        )
    except OSError:
        _LOGGER.exception("Could not initialize Tellstick")
        return False

    # Get all devices, switches and lights alike
    tellcore_devices = tellcore_lib.devices()

    # Register devices
    hass.data[DATA_TELLSTICK] = {device.id: device for device in tellcore_devices}

    # Discover the lights
    _discover(
        hass,
        config,
        "light",
        [device.id for device in tellcore_devices if device.methods(TELLSTICK_DIM)],
    )

    # Discover the cover
    _discover(
        hass,
        config,
        "cover",
        [device.id for device in tellcore_devices if device.methods(TELLSTICK_UP)],
    )

    # Discover the switches
    _discover(
        hass,
        config,
        "switch",
        [
            device.id
            for device in tellcore_devices
            if (not device.methods(TELLSTICK_UP) and not device.methods(TELLSTICK_DIM))
        ],
    )

    @callback
    def async_handle_callback(tellcore_id, tellcore_command, tellcore_data, cid):
        """Handle the actual callback from Tellcore."""
        async_dispatcher_send(
            hass, SIGNAL_TELLCORE_CALLBACK, tellcore_id, tellcore_command, tellcore_data
        )

    # Register callback
    callback_id = tellcore_lib.register_device_event(async_handle_callback)

    def clean_up_callback(event):
        """Unregister the callback bindings."""
        if callback_id is not None:
            tellcore_lib.unregister_callback(callback_id)

    hass.bus.listen_once(EVENT_HOMEASSISTANT_STOP, clean_up_callback)

    return True