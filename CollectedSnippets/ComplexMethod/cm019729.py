async def test_switch_timer(
    hass: HomeAssistant,
    load_int: ConfigEntry,
    mock_client: MagicMock,
    freezer: FrozenDateTimeFactory,
) -> None:
    """Test the Sensibo switch timer."""

    state = hass.states.get("switch.hallway_timer")
    assert state.state == STATE_OFF
    assert state.attributes["id"] is None
    assert state.attributes["turn_on"] is None

    mock_client.async_set_timer.return_value = {
        "status": "success",
        "result": {"id": "SzTGE4oZ4D"},
    }

    await hass.services.async_call(
        SWITCH_DOMAIN,
        SERVICE_TURN_ON,
        {
            ATTR_ENTITY_ID: state.entity_id,
        },
        blocking=True,
    )

    mock_client.async_get_devices_data.return_value.parsed["ABC999111"].timer_on = True
    mock_client.async_get_devices_data.return_value.parsed[
        "ABC999111"
    ].timer_id = "SzTGE4oZ4D"
    mock_client.async_get_devices_data.return_value.parsed[
        "ABC999111"
    ].timer_state_on = False

    freezer.tick(timedelta(minutes=5))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    state = hass.states.get("switch.hallway_timer")
    assert state.state == STATE_ON
    assert state.attributes["id"] == "SzTGE4oZ4D"
    assert state.attributes["turn_on"] is False

    mock_client.async_del_timer.return_value = {
        "status": "success",
        "result": {"id": "SzTGE4oZ4D"},
    }

    await hass.services.async_call(
        SWITCH_DOMAIN,
        SERVICE_TURN_OFF,
        {
            ATTR_ENTITY_ID: state.entity_id,
        },
        blocking=True,
    )

    mock_client.async_get_devices_data.return_value.parsed["ABC999111"].timer_on = False

    freezer.tick(timedelta(minutes=5))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    state = hass.states.get("switch.hallway_timer")
    assert state.state == STATE_OFF