async def async_get_actions(
    hass: HomeAssistant, device_id: str
) -> list[dict[str, str]]:
    """List device actions for Alarm control panel devices."""
    registry = er.async_get(hass)
    actions = []

    # Get all the integrations entities for this device
    for entry in er.async_entries_for_device(registry, device_id):
        if entry.domain != DOMAIN:
            continue

        supported_features = get_supported_features(hass, entry.entity_id)

        base_action: dict = {
            CONF_DEVICE_ID: device_id,
            CONF_DOMAIN: DOMAIN,
            CONF_ENTITY_ID: entry.id,
        }

        # Add actions for each entity that belongs to this integration
        if supported_features & AlarmControlPanelEntityFeature.ARM_AWAY:
            actions.append({**base_action, CONF_TYPE: "arm_away"})
        if supported_features & AlarmControlPanelEntityFeature.ARM_HOME:
            actions.append({**base_action, CONF_TYPE: "arm_home"})
        if supported_features & AlarmControlPanelEntityFeature.ARM_NIGHT:
            actions.append({**base_action, CONF_TYPE: "arm_night"})
        if supported_features & AlarmControlPanelEntityFeature.ARM_VACATION:
            actions.append({**base_action, CONF_TYPE: "arm_vacation"})
        actions.append({**base_action, CONF_TYPE: "disarm"})
        if supported_features & AlarmControlPanelEntityFeature.TRIGGER:
            actions.append({**base_action, CONF_TYPE: "trigger"})

    return actions