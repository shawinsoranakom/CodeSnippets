async def test_reset_button(
    hass: HomeAssistant,
    mock_connection: AsyncMock,
    model: Model,
    entity_id: str,
    coils: dict[int, Any],
    freezer_ticker: Any,
) -> None:
    """Test reset button."""

    unit = UNIT_COILGROUPS[model.series]["main"]

    # Setup a non alarm state
    coils[unit.alarm_reset] = 0
    coils[unit.alarm] = 0

    await async_add_model(hass, model)

    state = hass.states.get(entity_id)
    assert state
    assert state.state == STATE_UNAVAILABLE

    # Signal alarm
    coils[unit.alarm] = 100

    await freezer_ticker(60)

    state = hass.states.get(entity_id)
    assert state
    assert state.state == STATE_UNKNOWN

    # Press button
    await hass.services.async_call(
        BUTTON_DOMAIN,
        SERVICE_PRESS,
        {ATTR_ENTITY_ID: entity_id},
        blocking=True,
    )
    await hass.async_block_till_done()

    # Verify reset was written
    args = mock_connection.write_coil.call_args
    assert args
    coil: CoilData = args.args[0]
    assert coil.coil.address == unit.alarm_reset
    assert coil.value == 1