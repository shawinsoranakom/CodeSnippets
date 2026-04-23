async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Qwiskswitch component setup."""

    # Add cmd's to in /&listen packets will fire events
    # By default only buttons of type [TOGGLE,SCENE EXE,LEVEL]
    cmd_buttons = set(CMD_BUTTONS)
    for btn in config[DOMAIN][CONF_BUTTON_EVENTS]:
        cmd_buttons.add(btn)

    url = config[DOMAIN][CONF_URL]
    dimmer_adjust = config[DOMAIN][CONF_DIMMER_ADJUST]
    sensors = config[DOMAIN][CONF_SENSORS]
    switches = config[DOMAIN][CONF_SWITCHES]

    def callback_value_changed(_qsd, qsid, _val):
        """Update entity values based on device change."""
        _LOGGER.debug("Dispatch %s (update from devices)", qsid)
        async_dispatcher_send(hass, qsid, None)

    session = async_get_clientsession(hass)
    qsusb = QSUsb(
        url=url,
        dim_adj=dimmer_adjust,
        session=session,
        callback_value_changed=callback_value_changed,
    )

    # Discover all devices in QSUSB
    if not await qsusb.update_from_devices():
        return False

    hass.data[DATA_QUIKSWITCH] = qsusb

    comps: dict[Platform, list] = {
        Platform.SWITCH: [],
        Platform.LIGHT: [],
        Platform.SENSOR: [],
        Platform.BINARY_SENSOR: [],
    }

    sensor_ids = []
    for sens in sensors:
        try:
            _, _type = SENSORS[sens["type"]]
            sensor_ids.append(sens["id"])
            if _type is bool:
                comps[Platform.BINARY_SENSOR].append(sens)
                continue
            comps[Platform.SENSOR].append(sens)
            for _key in ("invert", "class"):
                if _key in sens:
                    _LOGGER.warning(
                        "%s should only be used for binary_sensors: %s", _key, sens
                    )
        except KeyError:
            _LOGGER.warning(
                "Sensor validation failed for sensor id=%s type=%s",
                sens["id"],
                sens["type"],
            )

    for qsid, dev in qsusb.devices.items():
        if qsid in switches:
            if dev.qstype != QSType.relay:
                _LOGGER.warning("You specified a switch that is not a relay %s", qsid)
                continue
            comps[Platform.SWITCH].append(qsid)
        elif dev.qstype in (QSType.relay, QSType.dimmer):
            comps[Platform.LIGHT].append(qsid)
        else:
            _LOGGER.warning("Ignored unknown QSUSB device: %s", dev)
            continue

    # Load platforms
    for comp_name, comp_conf in comps.items():
        if comp_conf:
            load_platform(hass, comp_name, DOMAIN, {DOMAIN: comp_conf}, config)

    def callback_qs_listen(qspacket):
        """Typically a button press or update signal."""
        # If button pressed, fire a hass event
        if QS_ID in qspacket:
            if qspacket.get(QS_CMD, "") in cmd_buttons:
                hass.bus.async_fire(f"qwikswitch.button.{qspacket[QS_ID]}", qspacket)
                return

            if qspacket[QS_ID] in sensor_ids:
                _LOGGER.debug("Dispatch %s ((%s))", qspacket[QS_ID], qspacket)
                async_dispatcher_send(hass, qspacket[QS_ID], qspacket)

        # Update all ha_objects
        hass.async_create_task(qsusb.update_from_devices())

    @callback
    def async_start(_):
        """Start listening."""
        qsusb.listen(callback_qs_listen)

    hass.bus.async_listen_once(EVENT_HOMEASSISTANT_START, async_start)

    @callback
    def async_stop(_):
        """Stop the listener."""
        hass.data[DATA_QUIKSWITCH].stop()

    hass.bus.async_listen(EVENT_HOMEASSISTANT_STOP, async_stop)

    return True