async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: VenstarConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Venstar device sensors based on a config entry."""
    coordinator = config_entry.runtime_data
    entities: list[Entity] = []

    if sensors := coordinator.client.get_sensor_list():
        for sensor_name in sensors:
            entities.extend(
                [
                    VenstarSensor(coordinator, config_entry, description, sensor_name)
                    for description in SENSOR_ENTITIES
                    if coordinator.client.get_sensor(sensor_name, description.key)
                    is not None
                ]
            )

        runtimes = coordinator.runtimes[-1]
        for sensor_name in runtimes:
            if sensor_name in RUNTIME_DEVICES:
                entities.append(
                    VenstarSensor(
                        coordinator, config_entry, RUNTIME_ENTITY, sensor_name
                    )
                )
            entities.extend(
                VenstarSensor(coordinator, config_entry, description, sensor_name)
                for description in CONSUMABLE_ENTITIES
                if description.key == sensor_name
            )

    for description in INFO_ENTITIES:
        try:
            # just checking if the key exists
            coordinator.client.get_info(description.key)
        except KeyError:
            continue
        entities.append(
            VenstarSensor(coordinator, config_entry, description, description.key)
        )

    if entities:
        async_add_entities(entities)