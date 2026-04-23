async def test_media_player_eq_bands_not_supported(hass: HomeAssistant) -> None:
    """Test EqualizerController bands directive not supported."""
    device = (
        "media_player.test_bands",
        "on",
        {
            "friendly_name": "Test media player",
            "supported_features": MediaPlayerEntityFeature.SELECT_SOUND_MODE,
            "sound_mode": "tv",
            "sound_mode_list": ["movie", "music", "night", "sport", "tv", "rocknroll"],
        },
    )
    await discovery_test(device, hass)

    context = Context()

    # Test for SetBands Error
    request = get_new_request(
        "Alexa.EqualizerController", "SetBands", "media_player#test_bands"
    )
    request["directive"]["payload"] = {"bands": [{"name": "BASS", "value": -2}]}
    msg = await smart_home.async_handle_message(
        hass, get_default_config(hass), request, context
    )

    assert "event" in msg
    msg = msg["event"]
    assert msg["header"]["name"] == "ErrorResponse"
    assert msg["header"]["namespace"] == "Alexa"
    assert msg["payload"]["type"] == "INVALID_DIRECTIVE"

    # Test for AdjustBands Error
    request = get_new_request(
        "Alexa.EqualizerController", "AdjustBands", "media_player#test_bands"
    )
    request["directive"]["payload"] = {
        "bands": [{"name": "BASS", "levelDelta": 3, "levelDirection": "UP"}]
    }
    msg = await smart_home.async_handle_message(
        hass, get_default_config(hass), request, context
    )

    assert "event" in msg
    msg = msg["event"]
    assert msg["header"]["name"] == "ErrorResponse"
    assert msg["header"]["namespace"] == "Alexa"
    assert msg["payload"]["type"] == "INVALID_DIRECTIVE"

    # Test for ResetBands Error
    request = get_new_request(
        "Alexa.EqualizerController", "ResetBands", "media_player#test_bands"
    )
    request["directive"]["payload"] = {
        "bands": [{"name": "BASS", "levelDelta": 3, "levelDirection": "UP"}]
    }
    msg = await smart_home.async_handle_message(
        hass, get_default_config(hass), request, context
    )

    assert "event" in msg
    msg = msg["event"]
    assert msg["header"]["name"] == "ErrorResponse"
    assert msg["header"]["namespace"] == "Alexa"
    assert msg["payload"]["type"] == "INVALID_DIRECTIVE"