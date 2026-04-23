def async_setup_block_attribute_entities(
    hass: HomeAssistant,
    async_add_entities: AddEntitiesCallback,
    coordinator: ShellyBlockCoordinator,
    sensors: Mapping[tuple[str, str], BlockEntityDescription],
    sensor_class: Callable,
) -> None:
    """Set up entities for block attributes."""
    entities = []

    assert coordinator.device.blocks

    for block in coordinator.device.blocks:
        for sensor_id in block.sensor_ids:
            description = sensors.get((block.type, sensor_id))
            if description is None:
                continue

            # Filter out non-existing sensors and sensors without a value
            if description.models and coordinator.model not in description.models:
                continue

            if getattr(block, sensor_id, None) is None:
                continue

            # Filter and remove entities that according to settings
            # should not create an entity
            if description.removal_condition and description.removal_condition(
                coordinator.device.settings, block
            ):
                domain = sensor_class.__module__.split(".")[-1]
                unique_id = sensor_class(
                    coordinator, block, sensor_id, description
                ).unique_id
                LOGGER.debug("Removing Shelly entity with unique_id: %s", unique_id)
                async_remove_shelly_entity(hass, domain, unique_id)
            else:
                entities.append(
                    sensor_class(coordinator, block, sensor_id, description)
                )

    if not entities:
        return

    async_add_entities(entities)