async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Perform the setup for Xiaomi devices."""
    entities = []
    # Uses legacy hass.data[DOMAIN] pattern
    # pylint: disable-next=hass-use-runtime-data
    gateway = hass.data[DOMAIN][GATEWAYS_KEY][config_entry.entry_id]
    for device in gateway.devices["switch"]:
        model = device["model"]
        if model == "plug":
            if "proto" not in device or int(device["proto"][0:1]) == 1:
                data_key = "status"
            else:
                data_key = "channel_0"
            entities.append(
                XiaomiGenericSwitch(
                    device, "Plug", data_key, True, gateway, config_entry
                )
            )
        elif model in (
            "ctrl_neutral1",
            "ctrl_neutral1.aq1",
            "switch_b1lacn02",
            "switch.b1lacn02",
        ):
            entities.append(
                XiaomiGenericSwitch(
                    device, "Wall Switch", "channel_0", False, gateway, config_entry
                )
            )
        elif model in (
            "ctrl_ln1",
            "ctrl_ln1.aq1",
            "switch_b1nacn02",
            "switch.b1nacn02",
        ):
            entities.append(
                XiaomiGenericSwitch(
                    device, "Wall Switch LN", "channel_0", False, gateway, config_entry
                )
            )
        elif model in (
            "ctrl_neutral2",
            "ctrl_neutral2.aq1",
            "switch_b2lacn02",
            "switch.b2lacn02",
        ):
            entities.append(
                XiaomiGenericSwitch(
                    device,
                    "Wall Switch Left",
                    "channel_0",
                    False,
                    gateway,
                    config_entry,
                )
            )
            entities.append(
                XiaomiGenericSwitch(
                    device,
                    "Wall Switch Right",
                    "channel_1",
                    False,
                    gateway,
                    config_entry,
                )
            )
        elif model in (
            "ctrl_ln2",
            "ctrl_ln2.aq1",
            "switch_b2nacn02",
            "switch.b2nacn02",
        ):
            entities.append(
                XiaomiGenericSwitch(
                    device,
                    "Wall Switch LN Left",
                    "channel_0",
                    False,
                    gateway,
                    config_entry,
                )
            )
            entities.append(
                XiaomiGenericSwitch(
                    device,
                    "Wall Switch LN Right",
                    "channel_1",
                    False,
                    gateway,
                    config_entry,
                )
            )
        elif model in ("86plug", "ctrl_86plug", "ctrl_86plug.aq1"):
            if "proto" not in device or int(device["proto"][0:1]) == 1:
                data_key = "status"
            else:
                data_key = "channel_0"
            entities.append(
                XiaomiGenericSwitch(
                    device, "Wall Plug", data_key, True, gateway, config_entry
                )
            )
    async_add_entities(entities)