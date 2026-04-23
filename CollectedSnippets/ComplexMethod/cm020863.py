async def test_cover_callbacks(
    hass: HomeAssistant,
    mock_airtouch5_client: AsyncMock,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Test the callbacks of the Airtouch5 covers."""

    await setup_integration(hass, mock_config_entry)

    # Capture initial state of zone 2 cover to verify it's unaffected
    zone_2_initial = hass.states.get(COVER_ZONE_2_ENTITY_ID)
    assert zone_2_initial
    zone_2_initial_state = zone_2_initial.state
    zone_2_initial_position = zone_2_initial.attributes.get(ATTR_CURRENT_POSITION)

    # Define a method to call all zone_status_callbacks, as the real client would
    async def _call_zone_status_callback(open_percentage: float) -> None:
        zsz = ZoneStatusZone(
            zone_power_state=ZonePowerState.ON,
            zone_number=1,
            control_method=ControlMethod.PERCENTAGE_CONTROL,
            open_percentage=open_percentage,
            set_point=None,
            has_sensor=False,
            temperature=None,
            spill_active=False,
            is_low_battery=False,
        )
        data = {1: zsz}
        for callback in mock_airtouch5_client.zone_status_callbacks:
            callback(data)
        await hass.async_block_till_done()

    # And call it to effectively launch the callback as the server would do

    # Partly open
    await _call_zone_status_callback(0.7)
    state = hass.states.get(COVER_ENTITY_ID)
    assert state
    assert state.state == CoverState.OPEN
    assert state.attributes.get(ATTR_CURRENT_POSITION) == 70
    zone_2 = hass.states.get(COVER_ZONE_2_ENTITY_ID)
    assert zone_2 and zone_2.state == zone_2_initial_state
    assert zone_2.attributes.get(ATTR_CURRENT_POSITION) == zone_2_initial_position

    # Fully open
    await _call_zone_status_callback(1)
    state = hass.states.get(COVER_ENTITY_ID)
    assert state
    assert state.state == CoverState.OPEN
    assert state.attributes.get(ATTR_CURRENT_POSITION) == 100
    zone_2 = hass.states.get(COVER_ZONE_2_ENTITY_ID)
    assert zone_2 and zone_2.state == zone_2_initial_state
    assert zone_2.attributes.get(ATTR_CURRENT_POSITION) == zone_2_initial_position

    # Fully closed
    await _call_zone_status_callback(0.0)
    state = hass.states.get(COVER_ENTITY_ID)
    assert state
    assert state.state == CoverState.CLOSED
    assert state.attributes.get(ATTR_CURRENT_POSITION) == 0
    zone_2 = hass.states.get(COVER_ZONE_2_ENTITY_ID)
    assert zone_2 and zone_2.state == zone_2_initial_state
    assert zone_2.attributes.get(ATTR_CURRENT_POSITION) == zone_2_initial_position

    # Partly reopened
    await _call_zone_status_callback(0.3)
    state = hass.states.get(COVER_ENTITY_ID)
    assert state
    assert state.state == CoverState.OPEN
    assert state.attributes.get(ATTR_CURRENT_POSITION) == 30
    zone_2 = hass.states.get(COVER_ZONE_2_ENTITY_ID)
    assert zone_2 and zone_2.state == zone_2_initial_state
    assert zone_2.attributes.get(ATTR_CURRENT_POSITION) == zone_2_initial_position