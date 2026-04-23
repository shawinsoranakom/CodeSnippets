async def test_media_player_speaker(hass: HomeAssistant) -> None:
    """Test media player with speaker interface."""
    device = (
        "media_player.test_speaker",
        "off",
        {
            "friendly_name": "Test media player speaker",
            "supported_features": MediaPlayerEntityFeature.VOLUME_MUTE
            | MediaPlayerEntityFeature.VOLUME_SET,
            "volume_level": 0.75,
            "device_class": "speaker",
        },
    )
    appliance = await discovery_test(device, hass)

    assert appliance["endpointId"] == "media_player#test_speaker"
    assert appliance["displayCategories"][0] == "SPEAKER"
    assert appliance["friendlyName"] == "Test media player speaker"

    capabilities = assert_endpoint_capabilities(
        appliance,
        "Alexa",
        "Alexa.EndpointHealth",
        "Alexa.PowerController",
        "Alexa.Speaker",
    )

    speaker_capability = get_capability(capabilities, "Alexa.Speaker")
    properties = speaker_capability["properties"]
    assert {"name": "volume"} in properties["supported"]
    assert {"name": "muted"} in properties["supported"]

    call, _ = await assert_request_calls_service(
        "Alexa.Speaker",
        "SetVolume",
        "media_player#test_speaker",
        "media_player.volume_set",
        hass,
        payload={"volume": 50},
    )
    assert call.data["volume_level"] == 0.5

    call, _ = await assert_request_calls_service(
        "Alexa.Speaker",
        "SetMute",
        "media_player#test_speaker",
        "media_player.volume_mute",
        hass,
        payload={"mute": True},
    )
    assert call.data["is_volume_muted"]

    (
        call,
        _,
    ) = await assert_request_calls_service(
        "Alexa.Speaker",
        "SetMute",
        "media_player#test_speaker",
        "media_player.volume_mute",
        hass,
        payload={"mute": False},
    )
    assert not call.data["is_volume_muted"]

    await assert_percentage_changes(
        hass,
        [(0.7, "-5"), (0.8, "5"), (0, "-80")],
        "Alexa.Speaker",
        "AdjustVolume",
        "media_player#test_speaker",
        "volume",
        "media_player.volume_set",
        "volume_level",
    )