async def async_setup_entry(
    hass: HomeAssistant,
    entry: BondConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Bond button devices."""
    data = entry.runtime_data
    entities: list[BondButtonEntity] = []

    for device in data.hub.devices:
        device_entities = [
            BondButtonEntity(data, device, description)
            for description in BUTTONS
            if device.has_action(description.key)
            and (
                description.mutually_exclusive is None
                or not device.has_action(description.mutually_exclusive)
            )
        ]
        if device_entities and device.has_action(STOP_BUTTON.key):
            # Most devices have the stop action available, but
            # we only add the stop action button if we add actions
            # since its not so useful if there are no actions to stop
            device_entities.append(BondButtonEntity(data, device, STOP_BUTTON))
        if device.has_action(PRESET_BUTTON.key):
            device_entities.append(BondButtonEntity(data, device, PRESET_BUTTON))
        entities.extend(device_entities)

    async_add_entities(entities)