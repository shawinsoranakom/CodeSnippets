async def test_update_unavailability_threshold(
    hass: HomeAssistant,
    freezer: FrozenDateTimeFactory,
    setup_entry: MockConfigEntry,
    fake_vacuum: FakeDevice,
) -> None:
    """Test that a small number of update failures are suppressed before marking a device unavailable."""
    await async_setup_component(hass, HA_DOMAIN, {})
    assert setup_entry.state is ConfigEntryState.LOADED

    # We pick an arbitrary sensor to test for availability
    sensor_entity_id = "sensor.roborock_s7_maxv_battery"
    expected_state = "100"
    state = hass.states.get(sensor_entity_id)
    assert state is not None
    assert state.state == expected_state

    # Simulate a few update failures below the threshold
    assert fake_vacuum.v1_properties is not None
    fake_vacuum.v1_properties.status.refresh.side_effect = RoborockException(
        "Simulated update failure"
    )

    # Move forward in time less than the threshold
    freezer.tick(datetime.timedelta(seconds=90))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    # Force a coordinator refresh.
    await hass.services.async_call(
        HA_DOMAIN,
        SERVICE_UPDATE_ENTITY,
        {ATTR_ENTITY_ID: sensor_entity_id},
        blocking=True,
    )
    await hass.async_block_till_done()

    # Verify that the entity is still available
    state = hass.states.get(sensor_entity_id)
    assert state is not None
    assert state.state == expected_state

    # Move forward in time to exceed the threshold
    freezer.tick(datetime.timedelta(minutes=3))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    # Verify that the entity is now unavailable
    state = hass.states.get(sensor_entity_id)
    assert state is not None
    assert state.state == "unavailable"

    # Now restore normal update behavior and refresh.
    fake_vacuum.v1_properties.status.refresh.side_effect = None

    freezer.tick(datetime.timedelta(seconds=45))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    # Verify that the entity recovers and is available again
    state = hass.states.get(sensor_entity_id)
    assert state is not None
    assert state.state == expected_state