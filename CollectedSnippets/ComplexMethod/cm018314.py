async def test_services(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
    mock_jellyfin: MagicMock,
    mock_api: MagicMock,
) -> None:
    """Test Jellyfin media player services."""
    state = hass.states.get("media_player.jellyfin_device")
    assert state

    await hass.services.async_call(
        MP_DOMAIN,
        "play_media",
        {
            ATTR_ENTITY_ID: state.entity_id,
            "media_content_type": "",
            "media_content_id": "ITEM-UUID",
        },
        blocking=True,
    )
    assert len(mock_api.remote_play_media.mock_calls) == 1
    assert mock_api.remote_play_media.mock_calls[0].args == (
        "SESSION-UUID",
        ["ITEM-UUID"],
        "PlayNow",
    )

    await hass.services.async_call(
        MP_DOMAIN,
        "media_pause",
        {
            ATTR_ENTITY_ID: state.entity_id,
        },
        blocking=True,
    )
    assert len(mock_api.remote_pause.mock_calls) == 1

    await hass.services.async_call(
        MP_DOMAIN,
        "media_play",
        {
            ATTR_ENTITY_ID: state.entity_id,
        },
        blocking=True,
    )
    assert len(mock_api.remote_unpause.mock_calls) == 1

    await hass.services.async_call(
        MP_DOMAIN,
        "media_play_pause",
        {
            ATTR_ENTITY_ID: state.entity_id,
        },
        blocking=True,
    )
    assert len(mock_api.remote_playpause.mock_calls) == 1

    await hass.services.async_call(
        MP_DOMAIN,
        "media_seek",
        {
            ATTR_ENTITY_ID: state.entity_id,
            "seek_position": 10,
        },
        blocking=True,
    )
    assert len(mock_api.remote_seek.mock_calls) == 1
    assert mock_api.remote_seek.mock_calls[0].args == (
        "SESSION-UUID",
        100000000,
    )

    await hass.services.async_call(
        MP_DOMAIN,
        "media_stop",
        {
            ATTR_ENTITY_ID: state.entity_id,
        },
        blocking=True,
    )
    assert len(mock_api.remote_stop.mock_calls) == 1

    await hass.services.async_call(
        MP_DOMAIN,
        "volume_set",
        {
            ATTR_ENTITY_ID: state.entity_id,
            "volume_level": 0.5,
        },
        blocking=True,
    )
    assert len(mock_api.remote_set_volume.mock_calls) == 1

    await hass.services.async_call(
        MP_DOMAIN,
        "volume_mute",
        {
            ATTR_ENTITY_ID: state.entity_id,
            "is_volume_muted": True,
        },
        blocking=True,
    )
    assert len(mock_api.remote_mute.mock_calls) == 1

    await hass.services.async_call(
        MP_DOMAIN,
        "volume_mute",
        {
            ATTR_ENTITY_ID: state.entity_id,
            "is_volume_muted": False,
        },
        blocking=True,
    )
    assert len(mock_api.remote_unmute.mock_calls) == 1