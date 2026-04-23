async def test_source_state_and_controls(
    hass: HomeAssistant,
    mock_receiver: MockReceiver,
    zone: ZoneName,
    entity_id: str,
    initial_source: str | None,
    updated_source: InputSource,
    expected_source: str,
    select_source_command: tuple[str, str],
) -> None:
    """Test source state and selection for each zone."""
    entity_state = hass.states.get(entity_id)

    assert entity_state.attributes.get(ATTR_INPUT_SOURCE) == initial_source

    source_list = entity_state.attributes[ATTR_INPUT_SOURCE_LIST]
    assert "cd" in source_list
    assert "dvd" in source_list
    assert "tuner" in source_list
    assert source_list == sorted(source_list)

    state = _default_state()
    zone_state = state.get_zone(zone)
    zone_state.power = True
    zone_state.input_source = updated_source
    mock_receiver.mock_state(state)
    await hass.async_block_till_done()

    assert hass.states.get(entity_id).attributes[ATTR_INPUT_SOURCE] == expected_source

    await hass.services.async_call(
        MP_DOMAIN,
        SERVICE_SELECT_SOURCE,
        {ATTR_ENTITY_ID: entity_id, ATTR_INPUT_SOURCE: expected_source},
        blocking=True,
    )
    assert mock_receiver._send_command.await_args == call(*select_source_command)