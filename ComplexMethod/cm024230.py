async def test_device_tracker_discovery_update(
    hass: HomeAssistant,
    mqtt_mock_entry: MqttMockHAClientGenerator,
    freezer: FrozenDateTimeFactory,
) -> None:
    """Test for a discovery update event."""
    freezer.move_to("2023-08-22 19:15:00+00:00")
    await mqtt_mock_entry()
    async_fire_mqtt_message(
        hass,
        "homeassistant/device_tracker/bla/config",
        '{ "name": "Beer", "state_topic": "test-topic" }',
    )
    await hass.async_block_till_done()

    state = hass.states.get("device_tracker.beer")
    assert state is not None
    assert state.name == "Beer"
    assert state.last_updated == datetime(2023, 8, 22, 19, 15, tzinfo=UTC)

    freezer.move_to("2023-08-22 19:16:00+00:00")
    async_fire_mqtt_message(
        hass,
        "homeassistant/device_tracker/bla/config",
        '{ "name": "Cider", "state_topic": "test-topic" }',
    )
    await hass.async_block_till_done()

    state = hass.states.get("device_tracker.beer")
    assert state is not None
    assert state.name == "Cider"
    assert state.last_updated == datetime(2023, 8, 22, 19, 16, tzinfo=UTC)

    freezer.move_to("2023-08-22 19:20:00+00:00")
    async_fire_mqtt_message(
        hass,
        "homeassistant/device_tracker/bla/config",
        '{ "name": "Cider", "state_topic": "test-topic" }',
    )
    await hass.async_block_till_done()

    state = hass.states.get("device_tracker.beer")
    assert state is not None
    assert state.name == "Cider"
    # Entity was not updated as the state was not changed
    assert state.last_updated == datetime(2023, 8, 22, 19, 16, tzinfo=UTC)

    await hass.async_block_till_done(wait_background_tasks=True)