async def async_get_triggers(
    hass: HomeAssistant, device_id: str
) -> list[dict[str, str]]:
    """List device triggers for Alarm control panel devices."""
    registry = er.async_get(hass)
    triggers: list[dict[str, str]] = []

    # Get all the integrations entities for this device
    for entry in er.async_entries_for_device(registry, device_id):
        if entry.domain != DOMAIN:
            continue

        supported_features = get_supported_features(hass, entry.entity_id)

        # Add triggers for each entity that belongs to this integration
        base_trigger = {
            CONF_PLATFORM: "device",
            CONF_DEVICE_ID: device_id,
            CONF_DOMAIN: DOMAIN,
            CONF_ENTITY_ID: entry.id,
        }

        triggers += [
            {
                **base_trigger,
                CONF_TYPE: trigger,
            }
            for trigger in BASIC_TRIGGER_TYPES
        ]
        if supported_features & AlarmControlPanelEntityFeature.ARM_HOME:
            triggers.append(
                {
                    **base_trigger,
                    CONF_TYPE: "armed_home",
                }
            )
        if supported_features & AlarmControlPanelEntityFeature.ARM_AWAY:
            triggers.append(
                {
                    **base_trigger,
                    CONF_TYPE: "armed_away",
                }
            )
        if supported_features & AlarmControlPanelEntityFeature.ARM_NIGHT:
            triggers.append(
                {
                    **base_trigger,
                    CONF_TYPE: "armed_night",
                }
            )
        if supported_features & AlarmControlPanelEntityFeature.ARM_VACATION:
            triggers.append(
                {
                    **base_trigger,
                    CONF_TYPE: "armed_vacation",
                }
            )

    return triggers