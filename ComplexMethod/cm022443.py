async def test_locate_vacuum(hass: HomeAssistant) -> None:
    """Test locate trait support for vacuum domain."""
    assert helpers.get_google_type(vacuum.DOMAIN, None) is not None
    assert trait.LocatorTrait.supported(
        vacuum.DOMAIN, VacuumEntityFeature.LOCATE, None, None
    )

    trt = trait.LocatorTrait(
        hass,
        State(
            "vacuum.bla",
            vacuum.VacuumActivity.IDLE,
            {ATTR_SUPPORTED_FEATURES: VacuumEntityFeature.LOCATE},
        ),
        BASIC_CONFIG,
    )

    assert trt.sync_attributes() == {}

    assert trt.query_attributes() == {}

    calls = async_mock_service(hass, vacuum.DOMAIN, vacuum.SERVICE_LOCATE)
    await trt.execute(trait.COMMAND_LOCATE, BASIC_DATA, {"silence": False}, {})
    assert len(calls) == 1
    assert calls[0].data == {ATTR_ENTITY_ID: "vacuum.bla"}

    with pytest.raises(helpers.SmartHomeError) as err:
        await trt.execute(trait.COMMAND_LOCATE, BASIC_DATA, {"silence": True}, {})
    assert err.value.code == const.ERR_FUNCTION_NOT_SUPPORTED