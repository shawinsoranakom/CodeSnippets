async def test_media_browse_local_source(
    hass: HomeAssistant,
    init_integration,
    mock_roku,
    hass_ws_client: WebSocketGenerator,
) -> None:
    """Test browsing local media source."""
    local_media = hass.config.path("media")
    await async_process_ha_core_config(
        hass, {"media_dirs": {"local": local_media, "recordings": local_media}}
    )
    await hass.async_block_till_done()

    assert await async_setup_component(hass, "media_source", {})
    await hass.async_block_till_done()

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
    assert msg["result"]["title"] == "Roku"
    assert msg["result"]["media_class"] == MediaClass.DIRECTORY
    assert msg["result"]["media_content_type"] == "root"
    assert msg["result"]["can_expand"]
    assert not msg["result"]["can_play"]
    assert len(msg["result"]["children"]) == 2

    assert msg["result"]["children"][0]["title"] == "Apps"
    assert msg["result"]["children"][0]["media_content_type"] == MediaType.APPS

    assert msg["result"]["children"][1]["title"] == "My media"
    assert msg["result"]["children"][1]["media_class"] == MediaClass.DIRECTORY
    assert msg["result"]["children"][1]["media_content_type"] is None
    assert (
        msg["result"]["children"][1]["media_content_id"]
        == "media-source://media_source"
    )
    assert not msg["result"]["children"][1]["can_play"]
    assert msg["result"]["children"][1]["can_expand"]

    # test local media
    await client.send_json(
        {
            "id": 2,
            "type": "media_player/browse_media",
            "entity_id": MAIN_ENTITY_ID,
            "media_content_type": "",
            "media_content_id": "media-source://media_source",
        }
    )

    msg = await client.receive_json()

    assert msg["id"] == 2
    assert msg["type"] == TYPE_RESULT
    assert msg["success"]

    assert msg["result"]
    assert msg["result"]["title"] == "My media"
    assert msg["result"]["media_class"] == MediaClass.DIRECTORY
    assert msg["result"]["media_content_type"] is None
    assert len(msg["result"]["children"]) == 2

    assert msg["result"]["children"][0]["title"] == "media"
    assert msg["result"]["children"][0]["media_content_type"] == ""
    assert (
        msg["result"]["children"][0]["media_content_id"]
        == "media-source://media_source/local/."
    )

    assert msg["result"]["children"][1]["title"] == "media"
    assert msg["result"]["children"][1]["media_content_type"] == ""
    assert (
        msg["result"]["children"][1]["media_content_id"]
        == "media-source://media_source/recordings/."
    )

    # test local media directory
    await client.send_json(
        {
            "id": 3,
            "type": "media_player/browse_media",
            "entity_id": MAIN_ENTITY_ID,
            "media_content_type": "",
            "media_content_id": "media-source://media_source/local/.",
        }
    )

    msg = await client.receive_json()

    assert msg["id"] == 3
    assert msg["type"] == TYPE_RESULT
    assert msg["success"]

    assert msg["result"]["title"] == "media"
    assert msg["result"]["media_class"] == MediaClass.DIRECTORY
    assert msg["result"]["media_content_type"] == ""
    assert len(msg["result"]["children"]) == 2

    assert msg["result"]["children"][0]["title"] == "Epic Sax Guy 10 Hours.mp4"
    assert msg["result"]["children"][0]["media_class"] == MediaClass.VIDEO
    assert msg["result"]["children"][0]["media_content_type"] == "video/mp4"
    assert (
        msg["result"]["children"][0]["media_content_id"]
        == "media-source://media_source/local/Epic Sax Guy 10 Hours.mp4"
    )