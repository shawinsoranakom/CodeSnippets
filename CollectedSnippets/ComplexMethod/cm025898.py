async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Perform the setup for Xiaomi devices."""
    entities: list[XiaomiSensor | XiaomiBatterySensor] = []
    # Uses legacy hass.data[DOMAIN] pattern
    # pylint: disable-next=hass-use-runtime-data
    gateway = hass.data[DOMAIN][GATEWAYS_KEY][config_entry.entry_id]
    for device in gateway.devices["sensor"]:
        if device["model"] == "sensor_ht":
            entities.append(
                XiaomiSensor(
                    device, "Temperature", "temperature", gateway, config_entry
                )
            )
            entities.append(
                XiaomiSensor(device, "Humidity", "humidity", gateway, config_entry)
            )
        elif device["model"] in ("weather", "weather.v1"):
            entities.append(
                XiaomiSensor(
                    device, "Temperature", "temperature", gateway, config_entry
                )
            )
            entities.append(
                XiaomiSensor(device, "Humidity", "humidity", gateway, config_entry)
            )
            entities.append(
                XiaomiSensor(device, "Pressure", "pressure", gateway, config_entry)
            )
        elif device["model"] == "sensor_motion.aq2":
            entities.append(
                XiaomiSensor(device, "Illumination", "lux", gateway, config_entry)
            )
        elif device["model"] in ("gateway", "gateway.v3", "acpartner.v3"):
            entities.append(
                XiaomiSensor(
                    device, "Illumination", "illumination", gateway, config_entry
                )
            )
        elif device["model"] == "vibration":
            entities.append(
                XiaomiSensor(
                    device, "Bed Activity", "bed_activity", gateway, config_entry
                )
            )
            entities.append(
                XiaomiSensor(
                    device, "Tilt Angle", "final_tilt_angle", gateway, config_entry
                )
            )
            entities.append(
                XiaomiSensor(
                    device, "Coordination", "coordination", gateway, config_entry
                )
            )
        else:
            _LOGGER.warning("Unmapped Device Model")

    # Set up battery sensors
    seen_sids = set()  # Set of device sids that are already seen
    for devices in gateway.devices.values():
        for device in devices:
            if device["sid"] in seen_sids:
                continue
            seen_sids.add(device["sid"])
            if device["model"] in BATTERY_MODELS:
                entities.append(
                    XiaomiBatterySensor(device, "Battery", gateway, config_entry)
                )
            if device["model"] in POWER_MODELS:
                entities.append(
                    XiaomiSensor(
                        device, "Load Power", "load_power", gateway, config_entry
                    )
                )
    async_add_entities(entities)