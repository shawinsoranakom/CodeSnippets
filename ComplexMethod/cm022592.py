async def test_number_when_control_missing(
    hass: HomeAssistant,
    mock_liebherr_client: MagicMock,
    freezer: FrozenDateTimeFactory,
) -> None:
    """Test number entity behavior when temperature control is removed."""
    entity_id = "number.test_fridge_top_zone_setpoint"

    # Initial values should be from the control
    state = hass.states.get(entity_id)
    assert state is not None
    assert state.state == "4"
    assert state.attributes["min"] == 2
    assert state.attributes["max"] == 8
    assert state.attributes["unit_of_measurement"] == "°C"

    # Device stops reporting controls
    mock_liebherr_client.get_device_state.side_effect = lambda *a, **kw: DeviceState(
        device=MOCK_DEVICE, controls=[]
    )

    # Advance time to trigger coordinator refresh
    freezer.tick(timedelta(seconds=61))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    # State should be unavailable
    state = hass.states.get(entity_id)
    assert state is not None
    assert state.state == STATE_UNAVAILABLE