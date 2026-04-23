async def test_startstop_vacuum(hass: HomeAssistant) -> None:
    """Test startStop trait support for vacuum domain."""
    assert helpers.get_google_type(vacuum.DOMAIN, None) is not None
    assert trait.StartStopTrait.supported(vacuum.DOMAIN, 0, None, None)

    trt = trait.StartStopTrait(
        hass,
        State(
            "vacuum.bla",
            vacuum.VacuumActivity.PAUSED,
            {ATTR_SUPPORTED_FEATURES: VacuumEntityFeature.PAUSE},
        ),
        BASIC_CONFIG,
    )

    assert trt.sync_attributes() == {"pausable": True}

    assert trt.query_attributes() == {"isRunning": False, "isPaused": True}

    start_calls = async_mock_service(hass, vacuum.DOMAIN, vacuum.SERVICE_START)
    await trt.execute(trait.COMMAND_START_STOP, BASIC_DATA, {"start": True}, {})
    assert len(start_calls) == 1
    assert start_calls[0].data == {ATTR_ENTITY_ID: "vacuum.bla"}

    stop_calls = async_mock_service(hass, vacuum.DOMAIN, vacuum.SERVICE_STOP)
    await trt.execute(trait.COMMAND_START_STOP, BASIC_DATA, {"start": False}, {})
    assert len(stop_calls) == 1
    assert stop_calls[0].data == {ATTR_ENTITY_ID: "vacuum.bla"}

    pause_calls = async_mock_service(hass, vacuum.DOMAIN, vacuum.SERVICE_PAUSE)
    await trt.execute(trait.COMMAND_PAUSE_UNPAUSE, BASIC_DATA, {"pause": True}, {})
    assert len(pause_calls) == 1
    assert pause_calls[0].data == {ATTR_ENTITY_ID: "vacuum.bla"}

    unpause_calls = async_mock_service(hass, vacuum.DOMAIN, vacuum.SERVICE_START)
    await trt.execute(trait.COMMAND_PAUSE_UNPAUSE, BASIC_DATA, {"pause": False}, {})
    assert len(unpause_calls) == 1
    assert unpause_calls[0].data == {ATTR_ENTITY_ID: "vacuum.bla"}