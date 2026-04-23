async def test_media_player(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    device_registry: dr.DeviceRegistry,
    mock_fully_kiosk: MagicMock,
    init_integration: MockConfigEntry,
) -> None:
    """Test standard Fully Kiosk media player."""
    state = hass.states.get("media_player.amazon_fire")
    assert state

    entry = entity_registry.async_get("media_player.amazon_fire")
    assert entry
    assert entry.unique_id == "abcdef-123456-mediaplayer"
    assert entry.supported_features == MEDIA_SUPPORT_FULLYKIOSK

    await hass.services.async_call(
        media_player.DOMAIN,
        "play_media",
        {
            ATTR_ENTITY_ID: "media_player.amazon_fire",
            "media_content_type": "music",
            "media_content_id": "test.mp3",
        },
        blocking=True,
    )
    assert len(mock_fully_kiosk.playSound.mock_calls) == 1

    with patch(
        "homeassistant.components.media_source.async_resolve_media",
        return_value=Mock(url="http://example.com/test.mp3"),
    ):
        await hass.services.async_call(
            "media_player",
            "play_media",
            {
                ATTR_ENTITY_ID: "media_player.amazon_fire",
                "media_content_id": "media-source://some_source/some_id",
                "media_content_type": "audio/mpeg",
            },
            blocking=True,
        )

        assert len(mock_fully_kiosk.playSound.mock_calls) == 2
        assert (
            mock_fully_kiosk.playSound.mock_calls[1].args[0]
            == "http://example.com/test.mp3"
        )

    await hass.services.async_call(
        media_player.DOMAIN,
        "media_stop",
        {
            ATTR_ENTITY_ID: "media_player.amazon_fire",
        },
        blocking=True,
    )
    assert len(mock_fully_kiosk.stopSound.mock_calls) == 1

    await hass.services.async_call(
        media_player.DOMAIN,
        "volume_set",
        {
            ATTR_ENTITY_ID: "media_player.amazon_fire",
            "volume_level": 0.5,
        },
        blocking=True,
    )
    assert len(mock_fully_kiosk.setAudioVolume.mock_calls) == 1

    assert entry.device_id
    device_entry = device_registry.async_get(entry.device_id)
    assert device_entry
    assert device_entry.configuration_url == "http://192.168.1.234:2323"
    assert device_entry.entry_type is None
    assert device_entry.hw_version is None
    assert device_entry.identifiers == {(DOMAIN, "abcdef-123456")}
    assert device_entry.manufacturer == "amzn"
    assert device_entry.model == "KFDOWI"
    assert device_entry.name == "Amazon Fire"
    assert device_entry.sw_version == "1.42.5"