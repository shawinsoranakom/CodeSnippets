async def async_setup_entry(
    hass: HomeAssistant,
    entry: SmartThingsConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Add button entities for a config entry."""
    entry_data = entry.runtime_data
    entities: list[SmartThingsEntity] = []
    entities.extend(
        SmartThingsButtonEntity(
            entry_data.client, device, description, Capability(capability), component
        )
        for capability, description in CAPABILITIES_TO_BUTTONS.items()
        for device in entry_data.devices.values()
        for component in description.components or [MAIN]
        if component in device.status and capability in device.status[component]
    )
    entities.extend(
        SmartThingsButtonEntity(
            entry_data.client,
            device,
            description,
            Capability.SAMSUNG_CE_DISHWASHER_OPERATION,
        )
        for device in entry_data.devices.values()
        if Capability.SAMSUNG_CE_DISHWASHER_OPERATION in device.status[MAIN]
        for description in DISHWASHER_OPERATION_COMMANDS_TO_BUTTONS.values()
    )
    entities.extend(
        SmartThingsButtonEntity(
            entry_data.client,
            device,
            DISHWASHER_CANCEL_AND_DRAIN_BUTTON,
            Capability.CUSTOM_SUPPORTED_OPTIONS,
        )
        for device in entry_data.devices.values()
        if (
            device.device.components[MAIN].manufacturer_category == Category.DISHWASHER
            and Capability.CUSTOM_SUPPORTED_OPTIONS in device.status[MAIN]
        )
    )
    async_add_entities(entities)