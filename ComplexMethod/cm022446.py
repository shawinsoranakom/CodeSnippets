async def test_startstop_lawn_mower(hass: HomeAssistant) -> None:
    """Test startStop trait support for lawn mower domain."""
    assert helpers.get_google_type(lawn_mower.DOMAIN, None) is not None
    assert trait.StartStopTrait.supported(lawn_mower.DOMAIN, 0, None, None)

    trt = trait.StartStopTrait(
        hass,
        State(
            "lawn_mower.bla",
            lawn_mower.LawnMowerActivity.PAUSED,
            {ATTR_SUPPORTED_FEATURES: LawnMowerEntityFeature.PAUSE},
        ),
        BASIC_CONFIG,
    )

    assert trt.sync_attributes() == {"pausable": True}

    assert trt.query_attributes() == {"isRunning": False, "isPaused": True}

    start_calls = async_mock_service(
        hass, lawn_mower.DOMAIN, lawn_mower.SERVICE_START_MOWING
    )
    await trt.execute(trait.COMMAND_START_STOP, BASIC_DATA, {"start": True}, {})
    assert len(start_calls) == 1
    assert start_calls[0].data == {ATTR_ENTITY_ID: "lawn_mower.bla"}

    pause_calls = async_mock_service(hass, lawn_mower.DOMAIN, lawn_mower.SERVICE_PAUSE)
    await trt.execute(trait.COMMAND_PAUSE_UNPAUSE, BASIC_DATA, {"pause": True}, {})
    assert len(pause_calls) == 1
    assert pause_calls[0].data == {ATTR_ENTITY_ID: "lawn_mower.bla"}

    unpause_calls = async_mock_service(
        hass, lawn_mower.DOMAIN, lawn_mower.SERVICE_START_MOWING
    )
    await trt.execute(trait.COMMAND_PAUSE_UNPAUSE, BASIC_DATA, {"pause": False}, {})
    assert len(unpause_calls) == 1
    assert unpause_calls[0].data == {ATTR_ENTITY_ID: "lawn_mower.bla"}