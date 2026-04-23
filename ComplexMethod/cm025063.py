async def test_translate_state(hass: HomeAssistant) -> None:
    """Test the state translation helper."""
    result = translation.async_translate_state(
        hass, "unavailable", "binary_sensor", "platform", "translation_key", None
    )
    assert result == "unavailable"

    result = translation.async_translate_state(
        hass, "unknown", "binary_sensor", "platform", "translation_key", None
    )
    assert result == "unknown"

    with patch(
        "homeassistant.helpers.translation.async_get_cached_translations",
        return_value={
            "component.platform.entity.binary_sensor.translation_key.state.on": "TRANSLATED"
        },
    ) as mock:
        result = translation.async_translate_state(
            hass, "on", "binary_sensor", "platform", "translation_key", None
        )
        mock.assert_called_once_with(hass, hass.config.language, "entity")
        assert result == "TRANSLATED"

    with patch(
        "homeassistant.helpers.translation.async_get_cached_translations",
        return_value={
            "component.binary_sensor.entity_component.device_class.state.on": "TRANSLATED"
        },
    ) as mock:
        result = translation.async_translate_state(
            hass, "on", "binary_sensor", "platform", None, "device_class"
        )
        mock.assert_called_once_with(hass, hass.config.language, "entity_component")
        assert result == "TRANSLATED"

    with patch(
        "homeassistant.helpers.translation.async_get_cached_translations",
        return_value={
            "component.binary_sensor.entity_component._.state.on": "TRANSLATED"
        },
    ) as mock:
        result = translation.async_translate_state(
            hass, "on", "binary_sensor", "platform", None, None
        )
        mock.assert_called_once_with(hass, hass.config.language, "entity_component")
        assert result == "TRANSLATED"

    with patch(
        "homeassistant.helpers.translation.async_get_cached_translations",
        return_value={},
    ) as mock:
        result = translation.async_translate_state(
            hass, "on", "binary_sensor", "platform", None, None
        )
        mock.assert_has_calls(
            [
                call(hass, hass.config.language, "entity_component"),
            ]
        )
        assert result == "on"

    with patch(
        "homeassistant.helpers.translation.async_get_cached_translations",
        return_value={},
    ) as mock:
        result = translation.async_translate_state(
            hass, "on", "binary_sensor", "platform", "translation_key", "device_class"
        )
        mock.assert_has_calls(
            [
                call(hass, hass.config.language, "entity"),
                call(hass, hass.config.language, "entity_component"),
            ]
        )
        assert result == "on"