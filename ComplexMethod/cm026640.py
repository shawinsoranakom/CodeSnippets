async def async_get_conditions(
    hass: HomeAssistant, device_id: str
) -> list[dict[str, str]]:
    """List device conditions for Alarm control panel devices."""
    registry = er.async_get(hass)
    conditions = []

    # Get all the integrations entities for this device
    for entry in er.async_entries_for_device(registry, device_id):
        if entry.domain != DOMAIN:
            continue

        supported_features = get_supported_features(hass, entry.entity_id)

        # Add conditions for each entity that belongs to this integration
        base_condition = {
            CONF_CONDITION: "device",
            CONF_DEVICE_ID: device_id,
            CONF_DOMAIN: DOMAIN,
            CONF_ENTITY_ID: entry.id,
        }

        conditions += [
            {**base_condition, CONF_TYPE: CONDITION_DISARMED},
            {**base_condition, CONF_TYPE: CONDITION_TRIGGERED},
        ]
        if supported_features & AlarmControlPanelEntityFeature.ARM_HOME:
            conditions.append({**base_condition, CONF_TYPE: CONDITION_ARMED_HOME})
        if supported_features & AlarmControlPanelEntityFeature.ARM_AWAY:
            conditions.append({**base_condition, CONF_TYPE: CONDITION_ARMED_AWAY})
        if supported_features & AlarmControlPanelEntityFeature.ARM_NIGHT:
            conditions.append({**base_condition, CONF_TYPE: CONDITION_ARMED_NIGHT})
        if supported_features & AlarmControlPanelEntityFeature.ARM_VACATION:
            conditions.append({**base_condition, CONF_TYPE: CONDITION_ARMED_VACATION})
        if supported_features & AlarmControlPanelEntityFeature.ARM_CUSTOM_BYPASS:
            conditions.append(
                {**base_condition, CONF_TYPE: CONDITION_ARMED_CUSTOM_BYPASS}
            )

    return conditions