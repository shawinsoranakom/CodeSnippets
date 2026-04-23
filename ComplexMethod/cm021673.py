async def test_media_player_eq_modes(hass: HomeAssistant) -> None:
    """Test media player discovery with sound mode list."""
    device = (
        "media_player.test",
        "on",
        {
            "friendly_name": "Test media player",
            "supported_features": MediaPlayerEntityFeature.SELECT_SOUND_MODE,
            "sound_mode": "tv",
            "sound_mode_list": ["movie", "music", "night", "sport", "tv", "rocknroll"],
        },
    )
    appliance = await discovery_test(device, hass)

    assert appliance["endpointId"] == "media_player#test"
    assert appliance["friendlyName"] == "Test media player"

    capabilities = assert_endpoint_capabilities(
        appliance,
        "Alexa",
        "Alexa.EqualizerController",
        "Alexa.PowerController",
        "Alexa.EndpointHealth",
    )

    eq_capability = get_capability(capabilities, "Alexa.EqualizerController")
    assert eq_capability is not None
    assert eq_capability["properties"]["retrievable"]
    assert "modes" in eq_capability["configurations"]

    eq_modes = eq_capability["configurations"]["modes"]
    assert {"name": "rocknroll"} not in eq_modes["supported"]
    assert {"name": "ROCKNROLL"} not in eq_modes["supported"]

    for mode in ("MOVIE", "MUSIC", "NIGHT", "SPORT", "TV"):
        assert {"name": mode} in eq_modes["supported"]

        call, _ = await assert_request_calls_service(
            "Alexa.EqualizerController",
            "SetMode",
            "media_player#test",
            "media_player.select_sound_mode",
            hass,
            payload={"mode": mode},
        )
        assert call.data["sound_mode"] == mode.lower()