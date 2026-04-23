async def test_openclose_cover_valve(
    hass: HomeAssistant,
    domain: str,
    set_position_service: str,
    close_service: str,
    open_service: str,
    set_position_feature: int,
    attr_position: str,
    attr_current_position: str,
) -> None:
    """Test OpenClose trait support."""
    assert helpers.get_google_type(domain, None) is not None
    assert trait.OpenCloseTrait.supported(domain, set_position_service, None, None)

    trt = trait.OpenCloseTrait(
        hass,
        State(
            f"{domain}.bla",
            "open",
            {
                attr_current_position: 75,
                ATTR_SUPPORTED_FEATURES: set_position_feature,
            },
        ),
        BASIC_CONFIG,
    )

    assert trt.sync_attributes() == {}
    assert trt.query_attributes() == {"openPercent": 75}

    calls_set = async_mock_service(hass, domain, set_position_service)
    calls_open = async_mock_service(hass, domain, open_service)
    calls_close = async_mock_service(hass, domain, close_service)

    await trt.execute(trait.COMMAND_OPEN_CLOSE, BASIC_DATA, {"openPercent": 50}, {})
    await trt.execute(
        trait.COMMAND_OPEN_CLOSE_RELATIVE, BASIC_DATA, {"openRelativePercent": 50}, {}
    )
    assert len(calls_set) == 1
    assert calls_set[0].data == {
        ATTR_ENTITY_ID: f"{domain}.bla",
        attr_position: 50,
    }
    calls_set.pop(0)

    assert len(calls_open) == 1
    assert calls_open[0].data == {ATTR_ENTITY_ID: f"{domain}.bla"}
    calls_open.pop(0)

    assert len(calls_close) == 0

    await trt.execute(trait.COMMAND_OPEN_CLOSE, BASIC_DATA, {"openPercent": 0}, {})
    await trt.execute(
        trait.COMMAND_OPEN_CLOSE_RELATIVE, BASIC_DATA, {"openRelativePercent": 0}, {}
    )
    assert len(calls_set) == 1
    assert len(calls_close) == 1
    assert calls_close[0].data == {ATTR_ENTITY_ID: f"{domain}.bla"}
    assert len(calls_open) == 0