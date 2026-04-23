async def async_setup_entry(
    hass: HomeAssistant,
    entry: OverkizDataConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the Overkiz climate from a config entry."""
    data = entry.runtime_data

    # Match devices based on the widget.
    entities_based_on_widget: list[Entity] = [
        WIDGET_TO_CLIMATE_ENTITY[device.widget](device.device_url, data.coordinator)
        for device in data.platforms[Platform.CLIMATE]
        if device.widget in WIDGET_TO_CLIMATE_ENTITY
    ]

    # Match devices based on the widget and controllableName.
    # ie Atlantic APC
    entities_based_on_widget_and_controllable: list[Entity] = [
        WIDGET_AND_CONTROLLABLE_TO_CLIMATE_ENTITY[device.widget][
            device.controllable_name  # type: ignore[index]
        ](device.device_url, data.coordinator)
        for device in data.platforms[Platform.CLIMATE]
        if device.widget in WIDGET_AND_CONTROLLABLE_TO_CLIMATE_ENTITY
        and device.controllable_name
        in WIDGET_AND_CONTROLLABLE_TO_CLIMATE_ENTITY[device.widget]
    ]

    # Match devices based on the widget and protocol.
    # #ie Hitachi Air To Air Heat Pumps
    entities_based_on_widget_and_protocol: list[Entity] = [
        WIDGET_AND_PROTOCOL_TO_CLIMATE_ENTITY[device.widget][device.protocol](
            device.device_url, data.coordinator
        )
        for device in data.platforms[Platform.CLIMATE]
        if device.widget in WIDGET_AND_PROTOCOL_TO_CLIMATE_ENTITY
        and device.protocol in WIDGET_AND_PROTOCOL_TO_CLIMATE_ENTITY[device.widget]
    ]

    async_add_entities(
        entities_based_on_widget
        + entities_based_on_widget_and_controllable
        + entities_based_on_widget_and_protocol
    )