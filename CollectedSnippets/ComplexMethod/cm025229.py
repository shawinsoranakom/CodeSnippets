async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: XiaomiMiioConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the Xiaomi light from a config entry."""
    entities: list[LightEntity] = []
    entity: LightEntity
    light: MiioDevice

    if config_entry.data[CONF_FLOW_TYPE] == CONF_GATEWAY:
        gateway = config_entry.runtime_data.gateway
        gateway_coordinators = config_entry.runtime_data.gateway_coordinators
        # Gateway light
        if gateway.model not in [
            GATEWAY_MODEL_AC_V1,
            GATEWAY_MODEL_AC_V2,
            GATEWAY_MODEL_AC_V3,
        ]:
            entities.append(
                XiaomiGatewayLight(gateway, config_entry.title, config_entry.unique_id)
            )
        # Gateway sub devices
        sub_devices = gateway.devices
        entities.extend(
            XiaomiGatewayBulb(gateway_coordinators[sub_device.sid])
            for sub_device in sub_devices.values()
            if sub_device.device_type == "LightBulb"
        )

    if config_entry.data[CONF_FLOW_TYPE] == CONF_DEVICE:
        if DATA_KEY not in hass.data:
            hass.data[DATA_KEY] = {}

        host = config_entry.data[CONF_HOST]
        token = config_entry.data[CONF_TOKEN]
        name = config_entry.title
        model = config_entry.data[CONF_MODEL]
        unique_id = config_entry.unique_id

        _LOGGER.debug("Initializing with host %s (token %s...)", host, token[:5])

        if model in MODELS_LIGHT_EYECARE:
            light = PhilipsEyecare(host, token)
            entity = XiaomiPhilipsEyecareLamp(name, light, config_entry, unique_id)
            entities.append(entity)
            hass.data[DATA_KEY][host] = entity

            entities.append(
                XiaomiPhilipsEyecareLampAmbientLight(
                    name, light, config_entry, unique_id
                )
            )
            # The ambient light doesn't expose additional services.
            # A hass.data[DATA_KEY] entry isn't needed.
        elif model in MODELS_LIGHT_CEILING:
            light = Ceil(host, token)
            entity = XiaomiPhilipsCeilingLamp(name, light, config_entry, unique_id)
            entities.append(entity)
            hass.data[DATA_KEY][host] = entity
        elif model in MODELS_LIGHT_MOON:
            light = PhilipsMoonlight(host, token)
            entity = XiaomiPhilipsMoonlightLamp(name, light, config_entry, unique_id)
            entities.append(entity)
            hass.data[DATA_KEY][host] = entity
        elif model in MODELS_LIGHT_BULB:
            light = PhilipsBulb(host, token)
            entity = XiaomiPhilipsBulb(name, light, config_entry, unique_id)
            entities.append(entity)
            hass.data[DATA_KEY][host] = entity
        elif model in MODELS_LIGHT_MONO:
            light = PhilipsBulb(host, token)
            entity = XiaomiPhilipsGenericLight(name, light, config_entry, unique_id)
            entities.append(entity)
            hass.data[DATA_KEY][host] = entity
        else:
            _LOGGER.error(
                (
                    "Unsupported device found! Please create an issue at "
                    "https://github.com/syssi/philipslight/issues "
                    "and provide the following data: %s"
                ),
                model,
            )
            return

        async def async_service_handler(service: ServiceCall) -> None:
            """Map services to methods on Xiaomi Philips Lights."""
            method = SERVICE_TO_METHOD[service.service]
            params = {
                key: value
                for key, value in service.data.items()
                if key != ATTR_ENTITY_ID
            }
            if entity_ids := service.data.get(ATTR_ENTITY_ID):
                target_devices = [
                    dev
                    for dev in hass.data[DATA_KEY].values()
                    if dev.entity_id in entity_ids
                ]
            else:
                target_devices = hass.data[DATA_KEY].values()

            update_tasks = []
            for target_device in target_devices:
                if not hasattr(target_device, method.method):
                    continue
                await getattr(target_device, method.method)(**params)
                update_tasks.append(
                    asyncio.create_task(target_device.async_update_ha_state(True))
                )

            if update_tasks:
                await asyncio.wait(update_tasks)

        for xiaomi_miio_service, method in SERVICE_TO_METHOD.items():
            schema = method.schema or XIAOMI_MIIO_SERVICE_SCHEMA
            hass.services.async_register(
                DOMAIN, xiaomi_miio_service, async_service_handler, schema=schema
            )

    async_add_entities(entities, update_before_add=True)