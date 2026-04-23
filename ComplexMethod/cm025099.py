async def test_state_translated(
    hass: HomeAssistant, entity_registry: er.EntityRegistry
) -> None:
    """Test state_translated method."""
    assert await async_setup_component(
        hass,
        "binary_sensor",
        {
            "binary_sensor": {
                "platform": "group",
                "name": "Grouped",
                "entities": ["binary_sensor.first", "binary_sensor.second"],
            }
        },
    )
    await hass.async_block_till_done()
    await translation._async_get_translations_cache(hass).async_load("en", set())

    hass.states.async_set("switch.without_translations", "on", attributes={})
    hass.states.async_set("binary_sensor.without_device_class", "on", attributes={})
    hass.states.async_set(
        "binary_sensor.with_device_class", "on", attributes={"device_class": "motion"}
    )
    hass.states.async_set(
        "binary_sensor.with_unknown_device_class",
        "on",
        attributes={"device_class": "unknown_class"},
    )
    hass.states.async_set(
        "some_domain.with_device_class_1",
        "off",
        attributes={"device_class": "some_device_class"},
    )
    hass.states.async_set(
        "some_domain.with_device_class_2",
        "foo",
        attributes={"device_class": "some_device_class"},
    )
    hass.states.async_set("domain.is_unavailable", "unavailable", attributes={})
    hass.states.async_set("domain.is_unknown", "unknown", attributes={})

    config_entry = MockConfigEntry(domain="light")
    config_entry.add_to_hass(hass)
    entity_registry.async_get_or_create(
        "light",
        "hue",
        "5678",
        config_entry=config_entry,
        translation_key="translation_key",
    )
    hass.states.async_set("light.hue_5678", "on", attributes={})

    result = render(hass, '{{ state_translated("switch.without_translations") }}')
    assert result == "on"

    result = render(
        hass, '{{ state_translated("binary_sensor.without_device_class") }}'
    )
    assert result == "On"

    result = render(hass, '{{ state_translated("binary_sensor.with_device_class") }}')
    assert result == "Detected"

    result = render(
        hass, '{{ state_translated("binary_sensor.with_unknown_device_class") }}'
    )
    assert result == "On"

    with pytest.raises(TemplateError):
        render(hass, '{{ state_translated("contextfunction") }}')

    result = render(hass, '{{ state_translated("switch.invalid") }}')
    assert result == "unknown"

    with pytest.raises(TemplateError):
        render(hass, '{{ state_translated("-invalid") }}')

    def mock_get_cached_translations(
        _hass: HomeAssistant,
        _language: str,
        category: str,
        _integrations: Iterable[str] | None = None,
    ):
        if category == "entity":
            return {
                "component.hue.entity.light.translation_key.state.on": "state_is_on",
            }
        return {}

    with patch(
        "homeassistant.helpers.translation.async_get_cached_translations",
        side_effect=mock_get_cached_translations,
    ):
        result = render(hass, '{{ state_translated("light.hue_5678") }}')
        assert result == "state_is_on"

    result = render(hass, '{{ state_translated("domain.is_unavailable") }}')
    assert result == "unavailable"

    result = render(hass, '{{ state_translated("domain.is_unknown") }}')
    assert result == "unknown"