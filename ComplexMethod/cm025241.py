async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: XiaomiMiioConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the Fan from a config entry."""
    entities: list[FanEntity] = []
    entity: FanEntity

    if config_entry.data[CONF_FLOW_TYPE] != CONF_DEVICE:
        return

    hass.data.setdefault(DATA_KEY, {})

    model = config_entry.data[CONF_MODEL]
    unique_id = config_entry.unique_id
    device = config_entry.runtime_data.device
    coordinator = config_entry.runtime_data.device_coordinator

    if model in (MODEL_AIRPURIFIER_3C, MODEL_AIRPURIFIER_3C_REV_A):
        entity = XiaomiAirPurifierMB4(
            device,
            config_entry,
            unique_id,
            coordinator,
        )
    elif model in MODELS_PURIFIER_MIOT:
        entity = XiaomiAirPurifierMiot(
            device,
            config_entry,
            unique_id,
            coordinator,
        )
    elif model.startswith("zhimi.airpurifier."):
        entity = XiaomiAirPurifier(device, config_entry, unique_id, coordinator)
    elif model.startswith("zhimi.airfresh."):
        entity = XiaomiAirFresh(device, config_entry, unique_id, coordinator)
    elif model == MODEL_AIRFRESH_A1:
        entity = XiaomiAirFreshA1(device, config_entry, unique_id, coordinator)
    elif model == MODEL_AIRFRESH_T2017:
        entity = XiaomiAirFreshT2017(device, config_entry, unique_id, coordinator)
    elif model == MODEL_FAN_P5:
        entity = XiaomiFanP5(device, config_entry, unique_id, coordinator)
    elif model in MODELS_FAN_MIIO:
        entity = XiaomiFan(device, config_entry, unique_id, coordinator)
    elif model == MODEL_FAN_ZA5:
        entity = XiaomiFanZA5(device, config_entry, unique_id, coordinator)
    elif model == MODEL_FAN_1C:
        entity = XiaomiFan1C(device, config_entry, unique_id, coordinator)
    elif model in MODELS_FAN_MIOT:
        entity = XiaomiFanMiot(device, config_entry, unique_id, coordinator)
    else:
        return

    hass.data[DATA_KEY][unique_id] = entity

    entities.append(entity)

    async def async_service_handler(service: ServiceCall) -> None:
        """Map services to methods on XiaomiAirPurifier."""
        method = SERVICE_TO_METHOD[service.service]
        params = {
            key: value for key, value in service.data.items() if key != ATTR_ENTITY_ID
        }
        if entity_ids := service.data.get(ATTR_ENTITY_ID):
            filtered_entities = [
                entity
                for entity in hass.data[DATA_KEY].values()
                if entity.entity_id in entity_ids
            ]
        else:
            filtered_entities = hass.data[DATA_KEY].values()

        update_tasks = []

        for entity in filtered_entities:
            entity_method = getattr(entity, method.method, None)
            if not entity_method:
                continue
            await entity_method(**params)
            update_tasks.append(asyncio.create_task(entity.async_update_ha_state(True)))

        if update_tasks:
            await asyncio.wait(update_tasks)

    for air_purifier_service, method in SERVICE_TO_METHOD.items():
        schema = method.schema or AIRPURIFIER_SERVICE_SCHEMA
        hass.services.async_register(
            DOMAIN, air_purifier_service, async_service_handler, schema=schema
        )

    async_add_entities(entities)