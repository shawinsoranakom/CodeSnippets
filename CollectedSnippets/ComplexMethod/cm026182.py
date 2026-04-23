async def async_setup_entry(
    hass: HomeAssistant,
    entry: MyStromConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the myStrom entities."""
    device = entry.runtime_data.device
    info = entry.runtime_data.info

    entities: list[MyStromSensorBase] = []
    match device:
        case MyStromPir():
            entities = [
                MyStromSensor(device, entry.title, description, info["mac"])
                for description in SENSOR_TYPES_PIR
                if description.value_fn(device) is not None
            ]
        case MyStromSwitch():
            entities = [
                MyStromSensor(device, entry.title, description, info["mac"])
                for description in SENSOR_TYPES_SWITCH
                if description.value_fn(device) is not None
            ]
            if device.time_since_boot is not None:
                entities.append(
                    MyStromSwitchUptimeSensor(device, entry.title, info["mac"])
                )
        case _:
            entities = []

    async_add_entities(entities)