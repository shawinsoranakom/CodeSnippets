async def test_browse_media_unfiltered(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    config_entry_mock: MockConfigEntry,
    dmr_device_mock: Mock,
    mock_entity_id: str,
) -> None:
    """Test the async_browse_media method with filtering turned off and on."""
    # Based on cast's test_entity_browse_media
    await async_setup_component(hass, MS_DOMAIN, {MS_DOMAIN: {}})
    await hass.async_block_till_done()

    expected_child_video = {
        "title": "Epic Sax Guy 10 Hours.mp4",
        "media_class": "video",
        "media_content_type": "video/mp4",
        "media_content_id": (
            "media-source://media_source/local/Epic Sax Guy 10 Hours.mp4"
        ),
        "can_play": True,
        "can_expand": False,
        "can_search": False,
        "thumbnail": None,
        "children_media_class": None,
    }
    expected_child_audio = {
        "title": "test.mp3",
        "media_class": "music",
        "media_content_type": "audio/mpeg",
        "media_content_id": "media-source://media_source/local/test.mp3",
        "can_play": True,
        "can_expand": False,
        "can_search": False,
        "thumbnail": None,
        "children_media_class": None,
    }

    # Device can only play MIME type audio/mpeg and audio/vorbis
    dmr_device_mock.sink_protocol_info = [
        "http-get:*:audio/mpeg:*",
        "http-get:*:audio/vorbis:*",
    ]

    # Filtering turned on by default
    assert CONF_BROWSE_UNFILTERED not in config_entry_mock.options

    client = await hass_ws_client()
    await client.send_json(
        {
            "id": 1,
            "type": "media_player/browse_media",
            "entity_id": mock_entity_id,
        }
    )
    response = await client.receive_json()
    assert response["success"]
    # Video file should not be shown
    assert expected_child_video not in response["result"]["children"]
    # Audio file should appear
    assert expected_child_audio in response["result"]["children"]

    # Filtering turned off via config entry
    hass.config_entries.async_update_entry(
        config_entry_mock,
        options={
            CONF_BROWSE_UNFILTERED: True,
        },
    )
    await hass.async_block_till_done()

    client = await hass_ws_client()
    await client.send_json(
        {
            "id": 1,
            "type": "media_player/browse_media",
            "entity_id": mock_entity_id,
        }
    )
    response = await client.receive_json()
    assert response["success"]
    # All files should be returned
    assert expected_child_video in response["result"]["children"]
    assert expected_child_audio in response["result"]["children"]