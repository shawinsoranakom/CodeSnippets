async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Perform the setup for Xiaomi devices."""
    entities: list[XiaomiBinarySensor] = []
    # Uses legacy hass.data[DOMAIN] pattern
    # pylint: disable-next=hass-use-runtime-data
    gateway = hass.data[DOMAIN][GATEWAYS_KEY][config_entry.entry_id]
    for entity in gateway.devices["binary_sensor"]:
        model = entity["model"]
        if model in ("motion", "sensor_motion", "sensor_motion.aq2"):
            entities.append(XiaomiMotionSensor(entity, hass, gateway, config_entry))
        elif model in ("magnet", "sensor_magnet", "sensor_magnet.aq2"):
            entities.append(XiaomiDoorSensor(entity, gateway, config_entry))
        elif model == "sensor_wleak.aq1":
            entities.append(XiaomiWaterLeakSensor(entity, gateway, config_entry))
        elif model in ("smoke", "sensor_smoke"):
            entities.append(XiaomiSmokeSensor(entity, gateway, config_entry))
        elif model in ("natgas", "sensor_natgas"):
            entities.append(XiaomiNatgasSensor(entity, gateway, config_entry))
        elif model in (
            "switch",
            "sensor_switch",
            "sensor_switch.aq2",
            "sensor_switch.aq3",
            "remote.b1acn01",
        ):
            if "proto" not in entity or int(entity["proto"][0:1]) == 1:
                data_key = "status"
            else:
                data_key = "button_0"
            entities.append(
                XiaomiButton(entity, "Switch", data_key, hass, gateway, config_entry)
            )
        elif model in (
            "86sw1",
            "sensor_86sw1",
            "sensor_86sw1.aq1",
            "remote.b186acn01",
            "remote.b186acn02",
        ):
            if "proto" not in entity or int(entity["proto"][0:1]) == 1:
                data_key = "channel_0"
            else:
                data_key = "button_0"
            entities.append(
                XiaomiButton(
                    entity, "Wall Switch", data_key, hass, gateway, config_entry
                )
            )
        elif model in (
            "86sw2",
            "sensor_86sw2",
            "sensor_86sw2.aq1",
            "remote.b286acn01",
            "remote.b286acn02",
        ):
            if "proto" not in entity or int(entity["proto"][0:1]) == 1:
                data_key_left = "channel_0"
                data_key_right = "channel_1"
            else:
                data_key_left = "button_0"
                data_key_right = "button_1"
            entities.append(
                XiaomiButton(
                    entity,
                    "Wall Switch (Left)",
                    data_key_left,
                    hass,
                    gateway,
                    config_entry,
                )
            )
            entities.append(
                XiaomiButton(
                    entity,
                    "Wall Switch (Right)",
                    data_key_right,
                    hass,
                    gateway,
                    config_entry,
                )
            )
            entities.append(
                XiaomiButton(
                    entity,
                    "Wall Switch (Both)",
                    "dual_channel",
                    hass,
                    gateway,
                    config_entry,
                )
            )
        elif model in ("cube", "sensor_cube", "sensor_cube.aqgl01"):
            entities.append(XiaomiCube(entity, hass, gateway, config_entry))
        elif model in ("vibration", "vibration.aq1"):
            entities.append(
                XiaomiVibration(entity, "Vibration", "status", gateway, config_entry)
            )
        else:
            _LOGGER.warning("Unmapped Device Model %s", model)

    async_add_entities(entities)