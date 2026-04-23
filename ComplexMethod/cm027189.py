def state_to_json(config: Config, state: State) -> dict[str, Any]:
    """Convert an entity to its Hue bridge JSON representation."""
    color_modes = state.attributes.get(light.ATTR_SUPPORTED_COLOR_MODES) or []
    unique_id = _entity_unique_id(state.entity_id)
    state_dict = get_entity_state_dict(config, state)

    json_state: dict[str, str | bool | int] = {
        HUE_API_STATE_ON: state_dict[STATE_ON],
        "reachable": state.state != STATE_UNAVAILABLE,
        "mode": "homeautomation",
    }
    retval: dict[str, str | dict[str, str | bool | int]] = {
        "state": json_state,
        "name": config.get_entity_name(state),
        "uniqueid": unique_id,
        "manufacturername": "Home Assistant",
        "swversion": "123",
    }
    is_light = state.domain == light.DOMAIN
    color_supported = is_light and light.color_supported(color_modes)
    color_temp_supported = is_light and light.color_temp_supported(color_modes)
    if color_supported and color_temp_supported:
        # Extended Color light (Zigbee Device ID: 0x0210)
        # Same as Color light, but which supports additional setting of color temperature
        retval["type"] = "Extended color light"
        retval["modelid"] = "HASS231"
        json_state.update(
            {
                HUE_API_STATE_BRI: state_dict[STATE_BRIGHTNESS],
                HUE_API_STATE_HUE: state_dict[STATE_HUE],
                HUE_API_STATE_SAT: state_dict[STATE_SATURATION],
                HUE_API_STATE_CT: state_dict[STATE_COLOR_TEMP],
                HUE_API_STATE_EFFECT: "none",
            }
        )
        if state_dict[STATE_HUE] > 0 or state_dict[STATE_SATURATION] > 0:
            json_state[HUE_API_STATE_COLORMODE] = "hs"
        else:
            json_state[HUE_API_STATE_COLORMODE] = "ct"
    elif color_supported:
        # Color light (Zigbee Device ID: 0x0200)
        # Supports on/off, dimming and color control (hue/saturation, enhanced hue, color loop and XY)
        retval["type"] = "Color light"
        retval["modelid"] = "HASS213"
        json_state.update(
            {
                HUE_API_STATE_BRI: state_dict[STATE_BRIGHTNESS],
                HUE_API_STATE_COLORMODE: "hs",
                HUE_API_STATE_HUE: state_dict[STATE_HUE],
                HUE_API_STATE_SAT: state_dict[STATE_SATURATION],
                HUE_API_STATE_EFFECT: "none",
            }
        )
    elif color_temp_supported:
        # Color temperature light (Zigbee Device ID: 0x0220)
        # Supports groups, scenes, on/off, dimming, and setting of a color temperature
        retval["type"] = "Color temperature light"
        retval["modelid"] = "HASS312"
        json_state.update(
            {
                HUE_API_STATE_COLORMODE: "ct",
                HUE_API_STATE_CT: state_dict[STATE_COLOR_TEMP],
                HUE_API_STATE_BRI: state_dict[STATE_BRIGHTNESS],
            }
        )
    elif state_supports_hue_brightness(state, color_modes):
        # Dimmable light (Zigbee Device ID: 0x0100)
        # Supports groups, scenes, on/off and dimming
        retval["type"] = "Dimmable light"
        retval["modelid"] = "HASS123"
        json_state.update({HUE_API_STATE_BRI: state_dict[STATE_BRIGHTNESS]})
    elif not config.lights_all_dimmable:
        # On/Off light (ZigBee Device ID: 0x0000)
        # Supports groups, scenes and on/off control
        retval["type"] = "On/Off light"
        retval["productname"] = "On/Off light"
        retval["modelid"] = "HASS321"
    else:
        # Dimmable light (Zigbee Device ID: 0x0100)
        # Supports groups, scenes, on/off and dimming
        # Reports fixed brightness for compatibility with Alexa.
        retval["type"] = "Dimmable light"
        retval["modelid"] = "HASS123"
        json_state.update({HUE_API_STATE_BRI: HUE_API_STATE_BRI_MAX})

    return retval