async def test_onoff_media_player(hass: HomeAssistant) -> None:
    """Test OnOff trait support for media_player domain."""
    assert helpers.get_google_type(media_player.DOMAIN, None) is not None
    assert trait.OnOffTrait.supported(media_player.DOMAIN, 0, None, None)

    trt_on = trait.OnOffTrait(hass, State("media_player.bla", STATE_ON), BASIC_CONFIG)

    assert trt_on.sync_attributes() == {}

    assert trt_on.query_attributes() == {"on": True}

    trt_off = trait.OnOffTrait(hass, State("media_player.bla", STATE_OFF), BASIC_CONFIG)

    assert trt_off.query_attributes() == {"on": False}

    on_calls = async_mock_service(hass, media_player.DOMAIN, SERVICE_TURN_ON)
    await trt_on.execute(trait.COMMAND_ON_OFF, BASIC_DATA, {"on": True}, {})
    assert len(on_calls) == 1
    assert on_calls[0].data == {ATTR_ENTITY_ID: "media_player.bla"}

    off_calls = async_mock_service(hass, media_player.DOMAIN, SERVICE_TURN_OFF)

    await trt_on.execute(trait.COMMAND_ON_OFF, BASIC_DATA, {"on": False}, {})
    assert len(off_calls) == 1
    assert off_calls[0].data == {ATTR_ENTITY_ID: "media_player.bla"}