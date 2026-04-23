async def test_dump_data(hass: HomeAssistant) -> None:
    """Test that we cache data."""
    states = [
        State("input_boolean.b0", "on"),
        State("input_boolean.b1", "on"),
        State("input_boolean.b2", "on"),
        State("input_boolean.b5", "unavailable", {"restored": True}),
    ]

    platform = MockEntityPlatform(hass, domain="input_boolean")
    entity = Entity()
    entity.hass = hass
    entity.entity_id = "input_boolean.b0"
    await platform.async_add_entities([entity])

    entity = RestoreEntity()
    entity.hass = hass
    entity.entity_id = "input_boolean.b1"
    await platform.async_add_entities([entity])

    data = async_get(hass)
    now = dt_util.utcnow()
    data.last_states = {
        "input_boolean.b0": StoredState(State("input_boolean.b0", "off"), None, now),
        "input_boolean.b1": StoredState(State("input_boolean.b1", "off"), None, now),
        "input_boolean.b2": StoredState(State("input_boolean.b2", "off"), None, now),
        "input_boolean.b3": StoredState(State("input_boolean.b3", "off"), None, now),
        "input_boolean.b4": StoredState(
            State("input_boolean.b4", "off"),
            None,
            datetime(1985, 10, 26, 1, 22, tzinfo=dt_util.UTC),
        ),
        "input_boolean.b5": StoredState(State("input_boolean.b5", "off"), None, now),
    }

    for state in states:
        hass.states.async_set(state.entity_id, state.state, state.attributes)

    with patch(
        "homeassistant.helpers.restore_state.Store.async_save"
    ) as mock_write_data:
        await data.async_dump_states()

    assert mock_write_data.called
    args = mock_write_data.mock_calls[0][1]
    written_states = args[0]

    for state in states:
        hass.states.async_remove(state.entity_id)
    # b0 should not be written, since it didn't extend RestoreEntity
    # b1 should be written, since it is present in the current run
    # b2 should not be written, since it is not registered with the helper
    # b3 should be written, since it is still not expired
    # b4 should not be written, since it is now expired
    # b5 should be written, since current state is restored by entity registry
    assert len(written_states) == 3
    state0 = json_round_trip(written_states[0])
    state1 = json_round_trip(written_states[1])
    state2 = json_round_trip(written_states[2])
    assert state0["state"]["entity_id"] == "input_boolean.b1"
    assert state0["state"]["state"] == "on"
    assert state1["state"]["entity_id"] == "input_boolean.b3"
    assert state1["state"]["state"] == "off"
    assert state2["state"]["entity_id"] == "input_boolean.b5"
    assert state2["state"]["state"] == "off"

    # Test that removed entities are not persisted
    await entity.async_remove()

    for state in states:
        hass.states.async_set(state.entity_id, state.state, state.attributes)

    with patch(
        "homeassistant.helpers.restore_state.Store.async_save"
    ) as mock_write_data:
        await data.async_dump_states()

    assert mock_write_data.called
    args = mock_write_data.mock_calls[0][1]
    written_states = args[0]
    assert len(written_states) == 2
    state0 = json_round_trip(written_states[0])
    state1 = json_round_trip(written_states[1])
    assert state0["state"]["entity_id"] == "input_boolean.b3"
    assert state0["state"]["state"] == "off"
    assert state1["state"]["entity_id"] == "input_boolean.b5"
    assert state1["state"]["state"] == "off"