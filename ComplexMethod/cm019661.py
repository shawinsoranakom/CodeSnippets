async def test_restore_number_restore_state(
    hass: HomeAssistant,
    hass_storage: dict[str, Any],
    native_max,
    native_min,
    native_value,
    native_value_type,
    extra_data,
) -> None:
    """Test RestoreNumber."""
    mock_restore_cache_with_extra_data(hass, ((State("text.test", ""), extra_data),))

    entity0 = MockRestoreText(
        native_max=native_max,
        native_min=native_min,
        name="Test",
        native_value=None,
    )
    setup_test_component_platform(hass, DOMAIN, [entity0])

    assert await async_setup_component(hass, "text", {"text": {"platform": "test"}})
    await hass.async_block_till_done()

    assert hass.states.get(entity0.entity_id)

    assert entity0.native_max == native_max
    assert entity0.native_min == native_min
    assert entity0.mode == TextMode.TEXT
    assert entity0.pattern is None
    assert entity0.native_value == native_value
    assert isinstance(entity0.native_value, native_value_type)