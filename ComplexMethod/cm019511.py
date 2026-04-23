async def test_alarm_control_panel(
    hass: HomeAssistant, canary, entity_registry: er.EntityRegistry
) -> None:
    """Test the creation and values of the alarm_control_panel for Canary."""

    online_device_at_home = mock_device(20, "Dining Room", True, "Canary Pro")

    mocked_location = mock_location(
        location_id=100,
        name="Home",
        is_celsius=True,
        is_private=False,
        mode=mock_mode(7, "standby"),
        devices=[online_device_at_home],
    )

    instance = canary.return_value
    instance.get_locations.return_value = [mocked_location]

    with patch("homeassistant.components.canary.PLATFORMS", ["alarm_control_panel"]):
        await init_integration(hass)

    entity_id = "alarm_control_panel.home"
    entity_entry = entity_registry.async_get(entity_id)
    assert entity_entry
    assert entity_entry.unique_id == "100"

    state = hass.states.get(entity_id)
    assert state
    assert state.state == STATE_UNKNOWN
    assert not state.attributes["private"]

    # test private system
    type(mocked_location).is_private = PropertyMock(return_value=True)

    await async_update_entity(hass, entity_id)
    await hass.async_block_till_done()

    state = hass.states.get(entity_id)
    assert state
    assert state.state == AlarmControlPanelState.DISARMED
    assert state.attributes["private"]

    type(mocked_location).is_private = PropertyMock(return_value=False)

    # test armed home
    type(mocked_location).mode = PropertyMock(
        return_value=mock_mode(4, LOCATION_MODE_HOME)
    )

    await async_update_entity(hass, entity_id)
    await hass.async_block_till_done()

    state = hass.states.get(entity_id)
    assert state
    assert state.state == AlarmControlPanelState.ARMED_HOME

    # test armed away
    type(mocked_location).mode = PropertyMock(
        return_value=mock_mode(5, LOCATION_MODE_AWAY)
    )

    await async_update_entity(hass, entity_id)
    await hass.async_block_till_done()

    state = hass.states.get(entity_id)
    assert state
    assert state.state == AlarmControlPanelState.ARMED_AWAY

    # test armed night
    type(mocked_location).mode = PropertyMock(
        return_value=mock_mode(6, LOCATION_MODE_NIGHT)
    )

    await async_update_entity(hass, entity_id)
    await hass.async_block_till_done()

    state = hass.states.get(entity_id)
    assert state
    assert state.state == AlarmControlPanelState.ARMED_NIGHT