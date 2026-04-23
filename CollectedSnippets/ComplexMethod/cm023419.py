async def test_tv_media_browse(
    hass: HomeAssistant,
    init_integration,
    mock_roku,
    hass_ws_client: WebSocketGenerator,
) -> None:
    """Test browsing media."""
    client = await hass_ws_client(hass)

    await client.send_json(
        {
            "id": 1,
            "type": "media_player/browse_media",
            "entity_id": TV_ENTITY_ID,
        }
    )

    msg = await client.receive_json()

    assert msg["id"] == 1
    assert msg["type"] == TYPE_RESULT
    assert msg["success"]

    assert msg["result"]
    assert msg["result"]["title"] == "Roku"
    assert msg["result"]["media_class"] == MediaClass.DIRECTORY
    assert msg["result"]["media_content_type"] == "root"
    assert msg["result"]["can_expand"]
    assert not msg["result"]["can_play"]
    assert len(msg["result"]["children"]) == 2

    # test apps
    await client.send_json(
        {
            "id": 2,
            "type": "media_player/browse_media",
            "entity_id": TV_ENTITY_ID,
            "media_content_type": MediaType.APPS,
            "media_content_id": "apps",
        }
    )

    msg = await client.receive_json()

    assert msg["id"] == 2
    assert msg["type"] == TYPE_RESULT
    assert msg["success"]

    assert msg["result"]
    assert msg["result"]["title"] == "Apps"
    assert msg["result"]["media_class"] == MediaClass.DIRECTORY
    assert msg["result"]["media_content_type"] == MediaType.APPS
    assert msg["result"]["children_media_class"] == MediaClass.APP
    assert msg["result"]["can_expand"]
    assert not msg["result"]["can_play"]
    assert len(msg["result"]["children"]) == 11
    assert msg["result"]["children_media_class"] == MediaClass.APP

    assert msg["result"]["children"][0]["title"] == "Satellite TV"
    assert msg["result"]["children"][0]["media_content_type"] == MediaType.APP
    assert msg["result"]["children"][0]["media_content_id"] == "tvinput.hdmi2"
    assert (
        msg["result"]["children"][0]["thumbnail"]
        == "http://192.168.1.160:8060/query/icon/tvinput.hdmi2"
    )
    assert msg["result"]["children"][0]["can_play"]

    assert msg["result"]["children"][3]["title"] == "Roku Channel Store"
    assert msg["result"]["children"][3]["media_content_type"] == MediaType.APP
    assert msg["result"]["children"][3]["media_content_id"] == "11"
    assert (
        msg["result"]["children"][3]["thumbnail"]
        == "http://192.168.1.160:8060/query/icon/11"
    )
    assert msg["result"]["children"][3]["can_play"]

    # test channels
    await client.send_json(
        {
            "id": 3,
            "type": "media_player/browse_media",
            "entity_id": TV_ENTITY_ID,
            "media_content_type": MediaType.CHANNELS,
            "media_content_id": "channels",
        }
    )

    msg = await client.receive_json()

    assert msg["id"] == 3
    assert msg["type"] == TYPE_RESULT
    assert msg["success"]

    assert msg["result"]
    assert msg["result"]["title"] == "TV Channels"
    assert msg["result"]["media_class"] == MediaClass.DIRECTORY
    assert msg["result"]["media_content_type"] == MediaType.CHANNELS
    assert msg["result"]["children_media_class"] == MediaClass.CHANNEL
    assert msg["result"]["can_expand"]
    assert not msg["result"]["can_play"]
    assert len(msg["result"]["children"]) == 4
    assert msg["result"]["children_media_class"] == MediaClass.CHANNEL

    assert msg["result"]["children"][0]["title"] == "WhatsOn (1.1)"
    assert msg["result"]["children"][0]["media_content_type"] == MediaType.CHANNEL
    assert msg["result"]["children"][0]["media_content_id"] == "1.1"
    assert msg["result"]["children"][0]["can_play"]