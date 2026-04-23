async def test_invalid_state_handling(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    setup_component: ComponentSetup,
    freezer: FrozenDateTimeFactory,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test handling of invalid states in trend sensor."""
    await setup_component(
        {
            "sample_duration": 10000,
            "min_gradient": 1,
            "max_samples": 25,
            "min_samples": 5,
        },
    )

    for val in (10, 20, 30, 40, 50, 60):
        freezer.tick(timedelta(seconds=2))
        hass.states.async_set("sensor.test_state", val)
        await hass.async_block_till_done()

    assert hass.states.get("binary_sensor.test_trend_sensor").state == STATE_ON

    # Set an invalid state
    hass.states.async_set("sensor.test_state", "invalid")
    await hass.async_block_till_done()

    # The trend sensor should handle the invalid state gracefully
    assert (sensor_state := hass.states.get("binary_sensor.test_trend_sensor"))
    assert sensor_state.state == STATE_ON

    # Check if a warning is logged
    assert (
        "Error processing sensor state change for entity_id=sensor.test_state, "
        "attribute=None, state=invalid: could not convert string to float: 'invalid'"
    ) in caplog.text

    # Set a valid state again
    hass.states.async_set("sensor.test_state", 50)
    await hass.async_block_till_done()

    # The trend sensor should return to a valid state
    assert (sensor_state := hass.states.get("binary_sensor.test_trend_sensor"))
    assert sensor_state.state == "on"