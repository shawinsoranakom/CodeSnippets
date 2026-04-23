async def async_modbus_setup(
    hass: HomeAssistant,
    config: ConfigType,
) -> bool:
    """Set up Modbus component."""

    if config[DOMAIN]:
        config[DOMAIN] = check_config(hass, config[DOMAIN])
        if not config[DOMAIN]:
            return False
    if DATA_MODBUS_HUBS in hass.data and config[DOMAIN] == []:
        hubs = hass.data[DATA_MODBUS_HUBS]
        for hub in hubs.values():
            if not await hub.async_setup():
                return False
        hub_collect = hass.data[DATA_MODBUS_HUBS]
    else:
        hass.data[DATA_MODBUS_HUBS] = hub_collect = {}

    for conf_hub in config[DOMAIN]:
        my_hub = ModbusHub(hass, conf_hub)
        hub_collect[conf_hub[CONF_NAME]] = my_hub

        # modbus needs to be activated before components are loaded
        # to avoid a racing problem
        if not await my_hub.async_setup():
            return False

        # load platforms
        for component, conf_key in PLATFORMS:
            if conf_key in conf_hub:
                hass.async_create_task(
                    async_load_platform(hass, component, DOMAIN, conf_hub, config)
                )

    async def async_stop_modbus(event: Event) -> None:
        """Stop Modbus service."""
        for client in hub_collect.values():
            await client.async_close()

    hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, async_stop_modbus)

    def _get_service_call_details(
        service: ServiceCall,
    ) -> tuple[ModbusHub, int, int]:
        """Return the details required to process the service call."""
        device_address = service.data.get(ATTR_SLAVE, service.data.get(ATTR_UNIT, 1))
        address = service.data[ATTR_ADDRESS]
        hub = hub_collect[service.data[ATTR_HUB]]
        return (hub, device_address, address)

    async def async_write_register(service: ServiceCall) -> None:
        """Write Modbus registers."""
        hub, device_address, address = _get_service_call_details(service)

        value = service.data[ATTR_VALUE]
        if isinstance(value, list):
            await hub.async_pb_call(
                device_address, address, value, CALL_TYPE_WRITE_REGISTERS
            )
        else:
            await hub.async_pb_call(
                device_address, address, value, CALL_TYPE_WRITE_REGISTER
            )

    async def async_write_coil(service: ServiceCall) -> None:
        """Write Modbus coil."""
        hub, device_address, address = _get_service_call_details(service)

        state = service.data[ATTR_STATE]

        if isinstance(state, list):
            await hub.async_pb_call(
                device_address, address, state, CALL_TYPE_WRITE_COILS
            )
        else:
            await hub.async_pb_call(
                device_address, address, state, CALL_TYPE_WRITE_COIL
            )

    for x_write in (
        (SERVICE_WRITE_REGISTER, async_write_register, ATTR_VALUE, cv.positive_int),
        (SERVICE_WRITE_COIL, async_write_coil, ATTR_STATE, cv.boolean),
    ):
        hass.services.async_register(
            DOMAIN,
            x_write[0],
            x_write[1],
            schema=vol.Schema(
                {
                    vol.Optional(ATTR_HUB, default=DEFAULT_HUB): cv.string,
                    vol.Exclusive(ATTR_SLAVE, "unit"): cv.positive_int,
                    vol.Exclusive(ATTR_UNIT, "unit"): cv.positive_int,
                    vol.Required(ATTR_ADDRESS): cv.positive_int,
                    vol.Required(x_write[2]): vol.Any(
                        cv.positive_int, vol.All(cv.ensure_list, [x_write[3]])
                    ),
                }
            ),
        )

    async def async_stop_hub(service: ServiceCall) -> None:
        """Stop Modbus hub."""
        async_dispatcher_send(hass, SIGNAL_STOP_ENTITY)
        hub = hub_collect[service.data[ATTR_HUB]]
        await hub.async_close()

    hass.services.async_register(
        DOMAIN,
        SERVICE_STOP,
        async_stop_hub,
        schema=vol.Schema({vol.Required(ATTR_HUB): cv.string}),
    )
    return True