async def async_setup_entry(
    hass: HomeAssistant,
    entry: SmartThingsConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Add switches for a config entry."""
    entry_data = entry.runtime_data
    entities: list[SmartThingsEntity] = [
        SmartThingsCommandSwitch(
            entry_data.client,
            device,
            description,
            Capability(capability),
        )
        for device in entry_data.devices.values()
        for capability, description in CAPABILITY_TO_COMMAND_SWITCHES.items()
        if capability in device.status[MAIN]
    ]
    entities.extend(
        SmartThingsSwitch(
            entry_data.client,
            device,
            description,
            Capability(capability),
            component,
        )
        for device in entry_data.devices.values()
        for capability, description in CAPABILITY_TO_SWITCHES.items()
        for component in device.status
        if capability in device.status[component]
        and (
            (description.component_translation_key is None and component == MAIN)
            or (
                description.component_translation_key is not None
                and component in description.component_translation_key
            )
        )
    )
    entities.extend(
        SmartThingsDishwasherWashingOptionSwitch(
            entry_data.client,
            device,
            DISHWASHER_WASHING_OPTIONS_TO_SWITCHES[attribute],
        )
        for device in entry_data.devices.values()
        for component in device.status
        if component == MAIN
        and Capability.SAMSUNG_CE_DISHWASHER_WASHING_OPTIONS in device.status[component]
        for attribute in cast(
            list[str],
            device.status[component][Capability.SAMSUNG_CE_DISHWASHER_WASHING_OPTIONS][
                Attribute.SUPPORTED_LIST
            ].value,
        )
        if attribute in DISHWASHER_WASHING_OPTIONS_TO_SWITCHES
    )
    entity_registry = er.async_get(hass)
    for device in entry_data.devices.values():
        if (
            Capability.SWITCH in device.status[MAIN]
            and not any(
                capability in device.status[MAIN] for capability in CAPABILITIES
            )
            and not all(
                capability in device.status[MAIN] for capability in AC_CAPABILITIES
            )
        ):
            media_player = all(
                capability in device.status[MAIN]
                for capability in MEDIA_PLAYER_CAPABILITIES
            )
            appliance = (
                device.device.components[MAIN].manufacturer_category
                in INVALID_SWITCH_CATEGORIES
            )
            dhw = Capability.SAMSUNG_CE_EHS_FSV_SETTINGS in device.status[MAIN]
            if media_player or appliance or dhw:
                if appliance:
                    issue = "appliance"
                    version = "2025.10.0"
                elif media_player:
                    issue = "media_player"
                    version = "2025.10.0"
                else:
                    issue = "dhw"
                    version = "2025.12.0"
                if deprecate_entity(
                    hass,
                    entity_registry,
                    SWITCH_DOMAIN,
                    f"{device.device.device_id}_{MAIN}_{Capability.SWITCH}_{Attribute.SWITCH}_{Attribute.SWITCH}",
                    f"deprecated_switch_{issue}",
                    version,
                ):
                    entities.append(
                        SmartThingsSwitch(
                            entry_data.client,
                            device,
                            SWITCH,
                            Capability.SWITCH,
                        )
                    )
                continue
            entities.append(
                SmartThingsSwitch(
                    entry_data.client,
                    device,
                    SWITCH,
                    Capability.SWITCH,
                )
            )
    async_add_entities(entities)