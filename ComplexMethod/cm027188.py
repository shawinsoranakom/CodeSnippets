def _build_entity_state_dict(entity: State) -> dict[str, Any]:
    """Build a state dict for an entity."""
    is_on = _hass_to_hue_state(entity)
    data: dict[str, Any] = {
        STATE_ON: is_on,
        STATE_BRIGHTNESS: None,
        STATE_HUE: None,
        STATE_SATURATION: None,
        STATE_COLOR_TEMP: None,
    }
    attributes = entity.attributes
    if is_on:
        data[STATE_BRIGHTNESS] = hass_to_hue_brightness(
            attributes.get(ATTR_BRIGHTNESS) or 0
        )
        if (hue_sat := attributes.get(ATTR_HS_COLOR)) is not None:
            hue = hue_sat[0]
            sat = hue_sat[1]
            # Convert hass hs values back to hue hs values
            data[STATE_HUE] = int((hue / 360.0) * HUE_API_STATE_HUE_MAX)
            data[STATE_SATURATION] = int((sat / 100.0) * HUE_API_STATE_SAT_MAX)
        else:
            data[STATE_HUE] = HUE_API_STATE_HUE_MIN
            data[STATE_SATURATION] = HUE_API_STATE_SAT_MIN
        kelvin = attributes.get(ATTR_COLOR_TEMP_KELVIN)
        data[STATE_COLOR_TEMP] = (
            color_util.color_temperature_kelvin_to_mired(kelvin)
            if kelvin is not None
            else 0
        )

    else:
        data[STATE_BRIGHTNESS] = 0
        data[STATE_HUE] = 0
        data[STATE_SATURATION] = 0
        data[STATE_COLOR_TEMP] = 0

    if entity.domain == climate.DOMAIN:
        temperature = attributes.get(ATTR_TEMPERATURE, 0)
        # Convert 0-100 to 0-254
        data[STATE_BRIGHTNESS] = round(temperature * HUE_API_STATE_BRI_MAX / 100)
    elif entity.domain == humidifier.DOMAIN:
        humidity = attributes.get(ATTR_HUMIDITY, 0)
        # Convert 0-100 to 0-254
        data[STATE_BRIGHTNESS] = round(humidity * HUE_API_STATE_BRI_MAX / 100)
    elif entity.domain == media_player.DOMAIN:
        level = attributes.get(ATTR_MEDIA_VOLUME_LEVEL, 1.0 if is_on else 0.0)
        # Convert 0.0-1.0 to 0-254
        data[STATE_BRIGHTNESS] = round(min(1.0, level) * HUE_API_STATE_BRI_MAX)
    elif entity.domain == fan.DOMAIN:
        percentage = attributes.get(ATTR_PERCENTAGE) or 0
        # Convert 0-100 to 0-254
        data[STATE_BRIGHTNESS] = round(percentage * HUE_API_STATE_BRI_MAX / 100)
    elif entity.domain == cover.DOMAIN:
        level = attributes.get(ATTR_CURRENT_POSITION, 0)
        data[STATE_BRIGHTNESS] = round(level / 100 * HUE_API_STATE_BRI_MAX)
    _clamp_values(data)
    return data