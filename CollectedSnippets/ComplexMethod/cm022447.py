async def test_startstop_cover_valve_no_assumed_state(
    hass: HomeAssistant,
    domain: str,
    state_open: str,
    state_closed: str,
    state_opening: str,
    state_closing: str,
    supported_features: str,
    service_open: str,
    service_close: str,
    service_stop: str,
    service_toggle: str,
) -> None:
    """Test startStop trait support and no assumed state."""
    assert helpers.get_google_type(domain, None) is not None
    assert trait.StartStopTrait.supported(domain, supported_features, None, None)

    state = State(
        f"{domain}.bla",
        state_closed,
        {ATTR_SUPPORTED_FEATURES: supported_features, ATTR_ASSUMED_STATE: False},
    )

    trt = trait.StartStopTrait(
        hass,
        state,
        BASIC_CONFIG,
    )

    assert trt.sync_attributes() == {}

    for state_value in (state_closing, state_opening):
        state.state = state_value
        assert trt.query_attributes() == {"isRunning": True}

    stop_calls = async_mock_service(hass, domain, service_stop)
    open_calls = async_mock_service(hass, domain, service_open)
    close_calls = async_mock_service(hass, domain, service_close)
    toggle_calls = async_mock_service(hass, domain, service_toggle)
    await trt.execute(trait.COMMAND_START_STOP, BASIC_DATA, {"start": False}, {})
    assert len(stop_calls) == 1
    assert stop_calls[0].data == {ATTR_ENTITY_ID: f"{domain}.bla"}

    for state_value in (state_closed, state_open):
        state.state = state_value
        assert trt.query_attributes() == {"isRunning": False}

    for state_value in (state_closing, state_opening):
        state.state = state_value
        assert trt.query_attributes() == {"isRunning": True}

    state.state = state_open
    with pytest.raises(
        SmartHomeError, match=f"{domain.capitalize()} is already stopped"
    ):
        await trt.execute(trait.COMMAND_START_STOP, BASIC_DATA, {"start": False}, {})

    # Start triggers toggle open
    state.state = state_closed
    await trt.execute(trait.COMMAND_START_STOP, BASIC_DATA, {"start": True}, {})
    assert len(open_calls) == 0
    assert len(close_calls) == 0
    assert len(toggle_calls) == 1
    assert toggle_calls[0].data == {ATTR_ENTITY_ID: f"{domain}.bla"}
    # Second start triggers toggle close
    state.state = state_open
    await trt.execute(trait.COMMAND_START_STOP, BASIC_DATA, {"start": True}, {})
    assert len(open_calls) == 0
    assert len(close_calls) == 0
    assert len(toggle_calls) == 2
    assert toggle_calls[1].data == {ATTR_ENTITY_ID: f"{domain}.bla"}

    state.state = state_closed
    with pytest.raises(
        SmartHomeError,
        match="Command action.devices.commands.PauseUnpause is not supported",
    ):
        await trt.execute(trait.COMMAND_PAUSE_UNPAUSE, BASIC_DATA, {"start": True}, {})