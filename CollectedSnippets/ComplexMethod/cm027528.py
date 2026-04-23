async def async_setup_entry(
    hass: HomeAssistant,
    entry: SmartThingsConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Add binary sensors for a config entry."""
    entry_data = entry.runtime_data

    async_add_entities(
        SmartThingsBinarySensor(
            entry_data.client,
            device,
            description,
            capability,
            attribute,
            component,
        )
        for device in entry_data.devices.values()
        for capability, attribute_map in CAPABILITY_TO_SENSORS.items()
        for attribute, description in attribute_map.items()
        for component in device.status
        if (
            capability in device.status[component]
            and (
                component == MAIN
                or (
                    description.component_translation_key is not None
                    and component in description.component_translation_key
                )
            )
            and (
                description.exists_fn is None
                or description.exists_fn(component, device.status)
            )
            and (
                not description.category
                or get_main_component_category(device) in description.category
            )
            and (
                not description.supported_states_attributes
                or (
                    isinstance(
                        options := device.status[component][capability][
                            description.supported_states_attributes
                        ].value,
                        list,
                    )
                    and len(options) == 2
                )
            )
        )
    )