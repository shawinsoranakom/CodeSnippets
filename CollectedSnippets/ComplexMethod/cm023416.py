async def test_media_browse(
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
            "entity_id": MAIN_ENTITY_ID,
        }
    )

    msg = await client.receive_json()

    assert msg["id"] == 1
    assert msg["type"] == TYPE_RESULT
    assert msg["success"]

    assert msg["result"]
    assert msg["result"]["title"] == "Apps"
    assert msg["result"]["media_class"] == MediaClass.DIRECTORY
    assert msg["result"]["media_content_type"] == MediaType.APPS
    assert msg["result"]["children_media_class"] == MediaClass.APP
    assert msg["result"]["can_expand"]
    assert not msg["result"]["can_play"]
    assert len(msg["result"]["children"]) == 8
    assert msg["result"]["children_media_class"] == MediaClass.APP

    assert msg["result"]["children"][0]["title"] == "Roku Channel Store"
    assert msg["result"]["children"][0]["media_content_type"] == MediaType.APP
    assert msg["result"]["children"][0]["media_content_id"] == "11"
    assert (
        msg["result"]["children"][0]["thumbnail"]
        == "http://192.168.1.160:8060/query/icon/11"
    )
    assert msg["result"]["children"][0]["can_play"]

    # test invalid media type
    await client.send_json(
        {
            "id": 2,
            "type": "media_player/browse_media",
            "entity_id": MAIN_ENTITY_ID,
            "media_content_type": "invalid",
            "media_content_id": "invalid",
        }
    )

    msg = await client.receive_json()

    assert msg["id"] == 2
    assert msg["type"] == TYPE_RESULT
    assert not msg["success"]