async def test_openclose_cover_secure(hass: HomeAssistant, device_class) -> None:
    """Test OpenClose trait support for cover domain."""
    assert helpers.get_google_type(cover.DOMAIN, device_class) is not None
    assert trait.OpenCloseTrait.supported(
        cover.DOMAIN, CoverEntityFeature.SET_POSITION, device_class, None
    )
    assert trait.OpenCloseTrait.might_2fa(
        cover.DOMAIN, CoverEntityFeature.SET_POSITION, device_class
    )

    trt = trait.OpenCloseTrait(
        hass,
        State(
            "cover.bla",
            cover.CoverState.OPEN,
            {
                ATTR_DEVICE_CLASS: device_class,
                ATTR_SUPPORTED_FEATURES: CoverEntityFeature.SET_POSITION,
                cover.ATTR_CURRENT_POSITION: 75,
            },
        ),
        PIN_CONFIG,
    )

    assert trt.sync_attributes() == {}
    assert trt.query_attributes() == {"openPercent": 75}

    calls = async_mock_service(hass, cover.DOMAIN, cover.SERVICE_SET_COVER_POSITION)
    calls_close = async_mock_service(hass, cover.DOMAIN, cover.SERVICE_CLOSE_COVER)

    # No challenge data
    with pytest.raises(error.ChallengeNeeded) as err:
        await trt.execute(trait.COMMAND_OPEN_CLOSE, PIN_DATA, {"openPercent": 50}, {})
    assert len(calls) == 0
    assert err.value.code == const.ERR_CHALLENGE_NEEDED
    assert err.value.challenge_type == const.CHALLENGE_PIN_NEEDED

    # invalid pin
    with pytest.raises(error.ChallengeNeeded) as err:
        await trt.execute(
            trait.COMMAND_OPEN_CLOSE, PIN_DATA, {"openPercent": 50}, {"pin": "9999"}
        )
    assert len(calls) == 0
    assert err.value.code == const.ERR_CHALLENGE_NEEDED
    assert err.value.challenge_type == const.CHALLENGE_FAILED_PIN_NEEDED

    await trt.execute(
        trait.COMMAND_OPEN_CLOSE, PIN_DATA, {"openPercent": 50}, {"pin": "1234"}
    )
    assert len(calls) == 1
    assert calls[0].data == {ATTR_ENTITY_ID: "cover.bla", cover.ATTR_POSITION: 50}

    # no challenge on close
    await trt.execute(trait.COMMAND_OPEN_CLOSE, PIN_DATA, {"openPercent": 0}, {})
    assert len(calls_close) == 1
    assert calls_close[0].data == {ATTR_ENTITY_ID: "cover.bla"}