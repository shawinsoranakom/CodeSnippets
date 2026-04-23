async def test_availability_json_attributes_without_value_template(
    hass: HomeAssistant,
    load_yaml_integration: None,
    freezer: FrozenDateTimeFactory,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test availability."""
    hass.states.async_set("sensor.input1", "on")
    freezer.tick(timedelta(minutes=1))
    async_fire_time_changed(hass)
    await hass.async_block_till_done(wait_background_tasks=True)

    entity_state = hass.states.get("sensor.test")
    assert entity_state
    assert entity_state.state == "unknown"
    assert entity_state.attributes["key"] == "value"
    assert entity_state.attributes["icon"] == "mdi:on"

    hass.states.async_set("sensor.input1", STATE_UNAVAILABLE)
    await hass.async_block_till_done()
    with mock_asyncio_subprocess_run(b"Not A Number"):
        freezer.tick(timedelta(minutes=1))
        async_fire_time_changed(hass)
        await hass.async_block_till_done(wait_background_tasks=True)

    assert "Unable to parse output as JSON" not in caplog.text

    entity_state = hass.states.get("sensor.test")
    assert entity_state
    assert entity_state.state == STATE_UNAVAILABLE
    assert "key" not in entity_state.attributes
    assert "icon" not in entity_state.attributes

    hass.states.async_set("sensor.input1", "on")
    await hass.async_block_till_done()
    with mock_asyncio_subprocess_run(b"Not A Number"):
        freezer.tick(timedelta(minutes=1))
        async_fire_time_changed(hass)
        await hass.async_block_till_done(wait_background_tasks=True)

    assert "Unable to parse output as JSON" in caplog.text

    async_fire_time_changed(hass)
    await hass.async_block_till_done(wait_background_tasks=True)
    with mock_asyncio_subprocess_run(b'{ "key": "value" }'):
        freezer.tick(timedelta(minutes=1))
        async_fire_time_changed(hass)
        await hass.async_block_till_done(wait_background_tasks=True)

    entity_state = hass.states.get("sensor.test")
    assert entity_state
    assert entity_state.state == "unknown"
    assert entity_state.attributes["key"] == "value"
    assert entity_state.attributes["icon"] == "mdi:on"