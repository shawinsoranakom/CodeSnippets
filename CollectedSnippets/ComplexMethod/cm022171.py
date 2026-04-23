async def test_cover_node_binary(
    hass: HomeAssistant,
    cover_node_binary: Sensor,
    receive_message: Callable[[str], None],
    transport_write: MagicMock,
) -> None:
    """Test a cover binary node."""
    entity_id = "cover.cover_node_1_1"

    state = hass.states.get(entity_id)

    assert state
    assert state.state == CoverState.CLOSED

    await hass.services.async_call(
        COVER_DOMAIN,
        SERVICE_OPEN_COVER,
        {ATTR_ENTITY_ID: entity_id},
        blocking=True,
    )

    assert transport_write.call_count == 1
    assert transport_write.call_args == call("1;1;1;1;29;1\n")

    receive_message("1;1;1;0;29;1\n")
    receive_message("1;1;1;0;2;1\n")
    await hass.async_block_till_done()

    state = hass.states.get(entity_id)

    assert state
    assert state.state == CoverState.OPENING

    transport_write.reset_mock()

    await hass.services.async_call(
        COVER_DOMAIN,
        SERVICE_STOP_COVER,
        {ATTR_ENTITY_ID: entity_id},
        blocking=True,
    )

    assert transport_write.call_count == 1
    assert transport_write.call_args == call("1;1;1;1;31;1\n")

    receive_message("1;1;1;0;31;1\n")
    await hass.async_block_till_done()

    state = hass.states.get(entity_id)

    assert state
    assert state.state == CoverState.OPEN

    transport_write.reset_mock()

    await hass.services.async_call(
        COVER_DOMAIN,
        SERVICE_OPEN_COVER,
        {ATTR_ENTITY_ID: entity_id},
        blocking=True,
    )

    assert transport_write.call_count == 1
    assert transport_write.call_args == call("1;1;1;1;29;1\n")

    receive_message("1;1;1;0;31;0\n")
    receive_message("1;1;1;0;29;1\n")
    await hass.async_block_till_done()

    state = hass.states.get(entity_id)

    assert state
    assert state.state == CoverState.OPENING

    receive_message("1;1;1;0;29;0\n")
    receive_message("1;1;1;0;2;1\n")
    await hass.async_block_till_done()

    state = hass.states.get(entity_id)

    assert state
    assert state.state == CoverState.OPEN

    transport_write.reset_mock()

    await hass.services.async_call(
        COVER_DOMAIN,
        SERVICE_CLOSE_COVER,
        {ATTR_ENTITY_ID: entity_id},
        blocking=True,
    )

    assert transport_write.call_count == 1
    assert transport_write.call_args == call("1;1;1;1;30;1\n")

    receive_message("1;1;1;0;30;1\n")
    await hass.async_block_till_done()

    state = hass.states.get(entity_id)

    assert state
    assert state.state == CoverState.CLOSING

    receive_message("1;1;1;0;30;0\n")
    receive_message("1;1;1;0;2;0\n")
    await hass.async_block_till_done()

    state = hass.states.get(entity_id)

    assert state
    assert state.state == CoverState.CLOSED