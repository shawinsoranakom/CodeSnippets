async def async_setup_entry(
    hass: HomeAssistant,
    entry: ProximityConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the proximity sensors."""

    coordinator = entry.runtime_data

    entities: list[ProximitySensor | ProximityTrackedEntitySensor] = [
        ProximitySensor(description, coordinator)
        for description in SENSORS_PER_PROXIMITY
    ]

    tracked_entity_descriptors: list[TrackedEntityDescriptor] = []

    entity_reg = er.async_get(hass)
    for tracked_entity_id in coordinator.tracked_entities:
        tracked_entity_object_id = tracked_entity_id.split(".")[-1]
        if (entity_entry := entity_reg.async_get(tracked_entity_id)) is not None:
            tracked_entity_descriptors.append(
                TrackedEntityDescriptor(
                    tracked_entity_id,
                    entity_entry.id,
                    entity_entry.name
                    or entity_entry.original_name
                    or tracked_entity_object_id,
                )
            )
        else:
            tracked_entity_descriptors.append(
                TrackedEntityDescriptor(
                    tracked_entity_id,
                    tracked_entity_id,
                    tracked_entity_object_id,
                )
            )

    entities += [
        ProximityTrackedEntitySensor(
            description, coordinator, tracked_entity_descriptor
        )
        for description in SENSORS_PER_ENTITY
        for tracked_entity_descriptor in tracked_entity_descriptors
    ]

    async_add_entities(entities)