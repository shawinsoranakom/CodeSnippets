async def test_services(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
    mock_roku: MagicMock,
) -> None:
    """Test the different media player services."""
    await hass.services.async_call(
        MP_DOMAIN, SERVICE_TURN_OFF, {ATTR_ENTITY_ID: MAIN_ENTITY_ID}, blocking=True
    )

    assert mock_roku.remote.call_count == 1
    mock_roku.remote.assert_called_with("poweroff")

    await hass.services.async_call(
        MP_DOMAIN, SERVICE_TURN_ON, {ATTR_ENTITY_ID: MAIN_ENTITY_ID}, blocking=True
    )

    assert mock_roku.remote.call_count == 2
    mock_roku.remote.assert_called_with("poweron")

    await hass.services.async_call(
        MP_DOMAIN,
        SERVICE_MEDIA_PAUSE,
        {ATTR_ENTITY_ID: MAIN_ENTITY_ID},
        blocking=True,
    )

    assert mock_roku.remote.call_count == 3
    mock_roku.remote.assert_called_with("play")

    await hass.services.async_call(
        MP_DOMAIN,
        SERVICE_MEDIA_PLAY,
        {ATTR_ENTITY_ID: MAIN_ENTITY_ID},
        blocking=True,
    )

    assert mock_roku.remote.call_count == 4
    mock_roku.remote.assert_called_with("play")

    await hass.services.async_call(
        MP_DOMAIN,
        SERVICE_MEDIA_PLAY_PAUSE,
        {ATTR_ENTITY_ID: MAIN_ENTITY_ID},
        blocking=True,
    )

    assert mock_roku.remote.call_count == 5
    mock_roku.remote.assert_called_with("play")

    await hass.services.async_call(
        MP_DOMAIN,
        SERVICE_MEDIA_NEXT_TRACK,
        {ATTR_ENTITY_ID: MAIN_ENTITY_ID},
        blocking=True,
    )

    assert mock_roku.remote.call_count == 6
    mock_roku.remote.assert_called_with("forward")

    await hass.services.async_call(
        MP_DOMAIN,
        SERVICE_MEDIA_PREVIOUS_TRACK,
        {ATTR_ENTITY_ID: MAIN_ENTITY_ID},
        blocking=True,
    )

    assert mock_roku.remote.call_count == 7
    mock_roku.remote.assert_called_with("reverse")

    await hass.services.async_call(
        MP_DOMAIN,
        SERVICE_SELECT_SOURCE,
        {ATTR_ENTITY_ID: MAIN_ENTITY_ID, ATTR_INPUT_SOURCE: "Home"},
        blocking=True,
    )

    assert mock_roku.remote.call_count == 8
    mock_roku.remote.assert_called_with("home")

    await hass.services.async_call(
        MP_DOMAIN,
        SERVICE_PLAY_MEDIA,
        {
            ATTR_ENTITY_ID: MAIN_ENTITY_ID,
            ATTR_MEDIA_CONTENT_TYPE: MediaType.APP,
            ATTR_MEDIA_CONTENT_ID: "11",
        },
        blocking=True,
    )

    assert mock_roku.launch.call_count == 1
    mock_roku.launch.assert_called_with("11", {})

    await hass.services.async_call(
        MP_DOMAIN,
        SERVICE_PLAY_MEDIA,
        {
            ATTR_ENTITY_ID: MAIN_ENTITY_ID,
            ATTR_MEDIA_CONTENT_TYPE: MediaType.APP,
            ATTR_MEDIA_CONTENT_ID: "291097",
            ATTR_MEDIA_EXTRA: {
                ATTR_MEDIA_TYPE: "movie",
                ATTR_CONTENT_ID: "8e06a8b7-d667-4e31-939d-f40a6dd78a88",
            },
        },
        blocking=True,
    )

    assert mock_roku.launch.call_count == 2
    mock_roku.launch.assert_called_with(
        "291097",
        {
            "contentID": "8e06a8b7-d667-4e31-939d-f40a6dd78a88",
            "mediaType": "movie",
        },
    )

    await hass.services.async_call(
        MP_DOMAIN,
        SERVICE_SELECT_SOURCE,
        {ATTR_ENTITY_ID: MAIN_ENTITY_ID, ATTR_INPUT_SOURCE: "Netflix"},
        blocking=True,
    )

    assert mock_roku.launch.call_count == 3
    mock_roku.launch.assert_called_with("12")

    await hass.services.async_call(
        MP_DOMAIN,
        SERVICE_SELECT_SOURCE,
        {ATTR_ENTITY_ID: MAIN_ENTITY_ID, ATTR_INPUT_SOURCE: 12},
        blocking=True,
    )

    assert mock_roku.launch.call_count == 4
    mock_roku.launch.assert_called_with("12")