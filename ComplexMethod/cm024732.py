async def test_availability(
    hass: HomeAssistant,
    load_yaml_integration: None,
    freezer: FrozenDateTimeFactory,
) -> None:
    """Test availability."""

    hass.states.async_set("sensor.input1", "on")
    freezer.tick(timedelta(minutes=1))
    async_fire_time_changed(hass)
    await hass.async_block_till_done(wait_background_tasks=True)

    entity_state = hass.states.get("cover.test")
    assert entity_state
    assert entity_state.state == CoverState.OPEN
    assert entity_state.attributes["icon"] == "mdi:on"

    hass.states.async_set("sensor.input1", STATE_UNAVAILABLE)
    await hass.async_block_till_done()
    with mock_asyncio_subprocess_run(b"50\n"):
        freezer.tick(timedelta(minutes=1))
        async_fire_time_changed(hass)
        await hass.async_block_till_done(wait_background_tasks=True)

    entity_state = hass.states.get("cover.test")
    assert entity_state
    assert entity_state.state == STATE_UNAVAILABLE
    assert "icon" not in entity_state.attributes

    hass.states.async_set("sensor.input1", "off")
    await hass.async_block_till_done()
    with mock_asyncio_subprocess_run(b"25\n"):
        freezer.tick(timedelta(minutes=1))
        async_fire_time_changed(hass)
        await hass.async_block_till_done(wait_background_tasks=True)

    entity_state = hass.states.get("cover.test")
    assert entity_state
    assert entity_state.state == CoverState.OPEN
    assert entity_state.attributes["icon"] == "mdi:off"