async def test_openclose_cover_valve_no_position(
    hass: HomeAssistant,
    domain: str,
    state_open: str,
    state_closed: str,
    supported_features: int,
    open_service: str,
    close_service: str,
) -> None:
    """Test OpenClose trait support."""
    assert helpers.get_google_type(domain, None) is not None
    assert trait.OpenCloseTrait.supported(
        domain,
        supported_features,
        None,
        None,
    )

    state = State(
        f"{domain}.bla",
        state_open,
        {
            ATTR_SUPPORTED_FEATURES: supported_features,
        },
    )

    trt = trait.OpenCloseTrait(
        hass,
        state,
        BASIC_CONFIG,
    )

    assert trt.sync_attributes() == {"discreteOnlyOpenClose": True}
    assert trt.query_attributes() == {"openPercent": 100}

    state.state = state_closed

    assert trt.sync_attributes() == {"discreteOnlyOpenClose": True}
    assert trt.query_attributes() == {"openPercent": 0}

    calls = async_mock_service(hass, domain, close_service)
    await trt.execute(trait.COMMAND_OPEN_CLOSE, BASIC_DATA, {"openPercent": 0}, {})
    assert len(calls) == 1
    assert calls[0].data == {ATTR_ENTITY_ID: f"{domain}.bla"}

    calls = async_mock_service(hass, domain, open_service)
    await trt.execute(trait.COMMAND_OPEN_CLOSE, BASIC_DATA, {"openPercent": 100}, {})
    assert len(calls) == 1
    assert calls[0].data == {ATTR_ENTITY_ID: f"{domain}.bla"}

    with pytest.raises(
        SmartHomeError, match=r"Current position not know for relative command"
    ):
        await trt.execute(
            trait.COMMAND_OPEN_CLOSE_RELATIVE,
            BASIC_DATA,
            {"openRelativePercent": 100},
            {},
        )

    with pytest.raises(SmartHomeError, match=r"No support for partial open close"):
        await trt.execute(trait.COMMAND_OPEN_CLOSE, BASIC_DATA, {"openPercent": 50}, {})