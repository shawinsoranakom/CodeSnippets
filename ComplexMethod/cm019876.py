async def test_cover_callbacks(
    hass: HomeAssistant,
    mock_dio_chacon_client: AsyncMock,
    mock_config_entry: MockConfigEntry,
    entity_registry: er.EntityRegistry,
) -> None:
    """Test the callbacks on the Chacon Dio covers."""

    await setup_integration(hass, mock_config_entry)

    # Server side callback tests
    # We find the callback method on the mock client
    callback_device_state_function: Callable = (
        mock_dio_chacon_client.set_callback_device_state_by_device.call_args[0][1]
    )

    # Define a method to simply call it
    async def _callback_device_state_function(open_level: int, movement: str) -> None:
        callback_device_state_function(
            {
                "id": "L4HActuator_idmock1",
                "connected": True,
                "openlevel": open_level,
                "movement": movement,
            }
        )
        await hass.async_block_till_done()

    # And call it to effectively launch the callback as the server would do
    await _callback_device_state_function(79, "stop")
    state = hass.states.get(COVER_ENTITY_ID)
    assert state
    assert state.attributes.get(ATTR_CURRENT_POSITION) == 79
    assert state.state == CoverState.OPEN

    await _callback_device_state_function(90, "up")
    state = hass.states.get(COVER_ENTITY_ID)
    assert state
    assert state.attributes.get(ATTR_CURRENT_POSITION) == 90
    assert state.state == CoverState.OPENING

    await _callback_device_state_function(60, "down")
    state = hass.states.get(COVER_ENTITY_ID)
    assert state
    assert state.attributes.get(ATTR_CURRENT_POSITION) == 60
    assert state.state == CoverState.CLOSING