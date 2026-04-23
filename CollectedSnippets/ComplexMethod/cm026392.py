async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the Broadlink switch."""
    device = hass.data[DOMAIN].devices[config_entry.entry_id]
    switches: list[BroadlinkSwitch] = []

    if device.api.type in {"RM4MINI", "RM4PRO", "RMMINI", "RMMINIB", "RMPRO"}:
        platform_data = hass.data[DOMAIN].platforms.setdefault(Platform.SWITCH, {})
        platform_data[device.api.mac] = async_add_entities, device
    elif device.api.type == "SP1":
        switches.append(BroadlinkSP1Switch(device))

    elif device.api.type in {"SP2", "SP2S", "SP3", "SP3S", "SP4", "SP4B"}:
        switches.append(BroadlinkSP2Switch(device))

    elif device.api.type == "BG1":
        switches.extend(BroadlinkBG1Slot(device, slot) for slot in range(1, 3))

    elif device.api.type in {"MP1", "MP1S"}:
        switches.extend(BroadlinkMP1Slot(device, slot) for slot in range(1, 5))

    async_add_entities(switches)