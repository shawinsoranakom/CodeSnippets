async def test_media_browse(
    hass: HomeAssistant, hass_ws_client: WebSocketGenerator
) -> None:
    """Test browsing media."""
    await async_setup_component(
        hass, "media_player", {"media_player": {"platform": "demo"}}
    )
    await hass.async_block_till_done()

    client = await hass_ws_client(hass)

    with patch(
        "homeassistant.components.demo.media_player.DemoBrowsePlayer.async_browse_media",
        return_value=BrowseMedia(
            media_class=MediaClass.DIRECTORY,
            media_content_id="mock-id",
            media_content_type="mock-type",
            title="Mock Title",
            can_play=False,
            can_expand=True,
        ),
    ) as mock_browse_media:
        await client.send_json(
            {
                "id": 5,
                "type": "media_player/browse_media",
                "entity_id": "media_player.browse",
                "media_content_type": "album",
                "media_content_id": "abcd",
            }
        )

        msg = await client.receive_json()

    assert msg["id"] == 5
    assert msg["type"] == TYPE_RESULT
    assert msg["success"]
    assert msg["result"] == {
        "title": "Mock Title",
        "media_class": "directory",
        "media_content_type": "mock-type",
        "media_content_id": "mock-id",
        "can_play": False,
        "can_expand": True,
        "can_search": False,
        "children_media_class": None,
        "thumbnail": None,
        "not_shown": 0,
        "children": [],
    }
    assert mock_browse_media.mock_calls[0][1] == ("album", "abcd")

    with patch(
        "homeassistant.components.demo.media_player.DemoBrowsePlayer.async_browse_media",
        return_value={"bla": "yo"},
    ):
        await client.send_json(
            {
                "id": 6,
                "type": "media_player/browse_media",
                "entity_id": "media_player.browse",
            }
        )

        msg = await client.receive_json()

    assert msg["id"] == 6
    assert msg["type"] == TYPE_RESULT
    assert msg["success"]
    assert msg["result"] == {"bla": "yo"}