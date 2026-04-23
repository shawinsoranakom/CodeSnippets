async def async_get_actions(
    hass: HomeAssistant, device_id: str
) -> list[dict[str, str]]:
    """List device actions for Cover devices."""
    registry = er.async_get(hass)
    actions = []

    # Get all the integrations entities for this device
    for entry in er.async_entries_for_device(registry, device_id):
        if entry.domain != DOMAIN:
            continue

        supported_features = get_supported_features(hass, entry.entity_id)

        # Add actions for each entity that belongs to this integration
        base_action = {
            CONF_DEVICE_ID: device_id,
            CONF_DOMAIN: DOMAIN,
            CONF_ENTITY_ID: entry.id,
        }

        if supported_features & CoverEntityFeature.SET_POSITION:
            actions.append({**base_action, CONF_TYPE: "set_position"})
        if supported_features & CoverEntityFeature.OPEN:
            actions.append({**base_action, CONF_TYPE: "open"})
        if supported_features & CoverEntityFeature.CLOSE:
            actions.append({**base_action, CONF_TYPE: "close"})
        if supported_features & CoverEntityFeature.STOP:
            actions.append({**base_action, CONF_TYPE: "stop"})

        if supported_features & CoverEntityFeature.SET_TILT_POSITION:
            actions.append({**base_action, CONF_TYPE: "set_tilt_position"})
        if supported_features & CoverEntityFeature.OPEN_TILT:
            actions.append({**base_action, CONF_TYPE: "open_tilt"})
        if supported_features & CoverEntityFeature.CLOSE_TILT:
            actions.append({**base_action, CONF_TYPE: "close_tilt"})

    return actions