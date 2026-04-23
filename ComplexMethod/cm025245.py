async def async_setup_other_entry(
    hass: HomeAssistant,
    config_entry: XiaomiMiioConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the other type switch from a config entry."""
    entities: list[SwitchEntity] = []
    host = config_entry.data[CONF_HOST]
    token = config_entry.data[CONF_TOKEN]
    name = config_entry.title
    model = config_entry.data[CONF_MODEL]
    unique_id = config_entry.unique_id
    if config_entry.data[CONF_FLOW_TYPE] == CONF_GATEWAY:
        gateway = config_entry.runtime_data.gateway
        gateway_coordinators = config_entry.runtime_data.gateway_coordinators
        # Gateway sub devices
        sub_devices = gateway.devices
        for sub_device in sub_devices.values():
            if sub_device.device_type != "Switch":
                continue
            switch_variables = set(sub_device.status) & set(GATEWAY_SWITCH_VARS)
            if switch_variables:
                entities.extend(
                    [
                        XiaomiGatewaySwitch(
                            gateway_coordinators[sub_device.sid], variable
                        )
                        for variable in switch_variables
                    ]
                )

    if config_entry.data[CONF_FLOW_TYPE] == CONF_DEVICE or (
        config_entry.data[CONF_FLOW_TYPE] == CONF_GATEWAY
        and model == "lumi.acpartner.v3"
    ):
        device: SwitchEntity
        if DATA_KEY not in hass.data:
            hass.data[DATA_KEY] = {}

        _LOGGER.debug("Initializing with host %s (token %s...)", host, token[:5])

        if model in ["chuangmi.plug.v1", "chuangmi.plug.v3", "chuangmi.plug.hmi208"]:
            chuangmi_plug = ChuangmiPlug(host, token, model=model)

            # The device has two switchable channels (mains and a USB port).
            # A switch device per channel will be created.
            for channel_usb in (True, False):
                if channel_usb:
                    unique_id_ch = f"{unique_id}-USB"
                else:
                    unique_id_ch = f"{unique_id}-mains"
                device = ChuangMiPlugSwitch(
                    name, chuangmi_plug, config_entry, unique_id_ch, channel_usb
                )
                entities.append(device)
                hass.data[DATA_KEY][host] = device
        elif model in ["qmi.powerstrip.v1", "zimi.powerstrip.v2"]:
            power_strip = PowerStrip(host, token, model=model)
            device = XiaomiPowerStripSwitch(name, power_strip, config_entry, unique_id)
            entities.append(device)
            hass.data[DATA_KEY][host] = device
        elif model in [
            "chuangmi.plug.m1",
            "chuangmi.plug.m3",
            "chuangmi.plug.v2",
            "chuangmi.plug.hmi205",
            "chuangmi.plug.hmi206",
        ]:
            chuangmi_plug = ChuangmiPlug(host, token, model=model)
            device = XiaomiPlugGenericSwitch(
                name, chuangmi_plug, config_entry, unique_id
            )
            entities.append(device)
            hass.data[DATA_KEY][host] = device
        elif model == "lumi.acpartner.v3":
            ac_companion = AirConditioningCompanionV3(host, token)
            device = XiaomiAirConditioningCompanionSwitch(
                name, ac_companion, config_entry, unique_id
            )
            entities.append(device)
            hass.data[DATA_KEY][host] = device
        else:
            _LOGGER.error(
                (
                    "Unsupported device found! Please create an issue at "
                    "https://github.com/rytilahti/python-miio/issues "
                    "and provide the following data: %s"
                ),
                model,
            )

        async def async_service_handler(service: ServiceCall) -> None:
            """Map services to methods on XiaomiPlugGenericSwitch."""
            method = SERVICE_TO_METHOD[service.service]
            params = {
                key: value
                for key, value in service.data.items()
                if key != ATTR_ENTITY_ID
            }
            if entity_ids := service.data.get(ATTR_ENTITY_ID):
                devices = [
                    device
                    for device in hass.data[DATA_KEY].values()
                    if device.entity_id in entity_ids
                ]
            else:
                devices = hass.data[DATA_KEY].values()

            update_tasks = []
            for device in devices:
                if not hasattr(device, method.method):
                    continue
                await getattr(device, method.method)(**params)
                update_tasks.append(
                    asyncio.create_task(device.async_update_ha_state(True))
                )

            if update_tasks:
                await asyncio.wait(update_tasks)

        for plug_service, method in SERVICE_TO_METHOD.items():
            schema = method.schema or SERVICE_SCHEMA
            hass.services.async_register(
                DOMAIN, plug_service, async_service_handler, schema=schema
            )

    async_add_entities(entities)