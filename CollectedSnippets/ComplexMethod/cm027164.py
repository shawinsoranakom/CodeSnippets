async def async_setup_entry(
    hass: HomeAssistant,
    entry: BondConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Bond light devices."""
    data = entry.runtime_data
    hub = data.hub

    fan_lights: list[Entity] = [
        BondLight(data, device)
        for device in hub.devices
        if DeviceType.is_fan(device.type)
        and device.supports_light()
        and not (device.supports_up_light() and device.supports_down_light())
    ]

    fan_up_lights: list[Entity] = [
        BondUpLight(data, device, "up_light")
        for device in hub.devices
        if DeviceType.is_fan(device.type) and device.supports_up_light()
    ]

    fan_down_lights: list[Entity] = [
        BondDownLight(data, device, "down_light")
        for device in hub.devices
        if DeviceType.is_fan(device.type) and device.supports_down_light()
    ]

    fireplaces: list[Entity] = [
        BondFireplace(data, device)
        for device in hub.devices
        if DeviceType.is_fireplace(device.type)
    ]

    fp_lights: list[Entity] = [
        BondLight(data, device, "light")
        for device in hub.devices
        if DeviceType.is_fireplace(device.type) and device.supports_light()
    ]

    lights: list[Entity] = [
        BondLight(data, device)
        for device in hub.devices
        if DeviceType.is_light(device.type)
    ]

    async_add_entities(
        fan_lights + fan_up_lights + fan_down_lights + fireplaces + fp_lights + lights,
    )