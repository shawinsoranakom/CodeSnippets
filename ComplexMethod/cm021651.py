async def test_media_player_seek(hass: HomeAssistant) -> None:
    """Test media player seek capability."""
    device = (
        "media_player.test_seek",
        "playing",
        {
            "friendly_name": "Test media player seek",
            "supported_features": MediaPlayerEntityFeature.SEEK,
            "media_position": 300,  # 5min
            "media_duration": 600,  # 10min
        },
    )
    appliance = await discovery_test(device, hass)

    assert appliance["endpointId"] == "media_player#test_seek"
    assert appliance["displayCategories"][0] == "TV"
    assert appliance["friendlyName"] == "Test media player seek"

    assert_endpoint_capabilities(
        appliance,
        "Alexa",
        "Alexa.EndpointHealth",
        "Alexa.PowerController",
        "Alexa.SeekController",
    )

    # Test seek forward 30 seconds.
    call, msg = await assert_request_calls_service(
        "Alexa.SeekController",
        "AdjustSeekPosition",
        "media_player#test_seek",
        "media_player.media_seek",
        hass,
        response_type="StateReport",
        payload={"deltaPositionMilliseconds": 30000},
    )
    assert call.data["seek_position"] == 330
    assert "properties" in msg["event"]["payload"]
    properties = msg["event"]["payload"]["properties"]
    assert {"name": "positionMilliseconds", "value": 330000} in properties

    # Test seek reverse 30 seconds.
    call, msg = await assert_request_calls_service(
        "Alexa.SeekController",
        "AdjustSeekPosition",
        "media_player#test_seek",
        "media_player.media_seek",
        hass,
        response_type="StateReport",
        payload={"deltaPositionMilliseconds": -30000},
    )
    assert call.data["seek_position"] == 270
    assert "properties" in msg["event"]["payload"]
    properties = msg["event"]["payload"]["properties"]
    assert {"name": "positionMilliseconds", "value": 270000} in properties

    # Test seek backwards more than current position (5 min.) result = 0.
    call, msg = await assert_request_calls_service(
        "Alexa.SeekController",
        "AdjustSeekPosition",
        "media_player#test_seek",
        "media_player.media_seek",
        hass,
        response_type="StateReport",
        payload={"deltaPositionMilliseconds": -500000},
    )
    assert call.data["seek_position"] == 0
    assert "properties" in msg["event"]["payload"]
    properties = msg["event"]["payload"]["properties"]
    assert {"name": "positionMilliseconds", "value": 0} in properties

    # Test seek forward more than current duration (10 min.) result = 600 sec.
    call, msg = await assert_request_calls_service(
        "Alexa.SeekController",
        "AdjustSeekPosition",
        "media_player#test_seek",
        "media_player.media_seek",
        hass,
        response_type="StateReport",
        payload={"deltaPositionMilliseconds": 800000},
    )
    assert call.data["seek_position"] == 600
    assert "properties" in msg["event"]["payload"]
    properties = msg["event"]["payload"]["properties"]
    assert {"name": "positionMilliseconds", "value": 600000} in properties