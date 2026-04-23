async def test_websocket_browse_media(
    hass: HomeAssistant, hass_ws_client: WebSocketGenerator
) -> None:
    """Test browse media websocket."""
    assert await async_setup_component(hass, media_source.DOMAIN, {})
    await hass.async_block_till_done()

    client = await hass_ws_client(hass)

    media = media_source.models.BrowseMediaSource(
        domain=media_source.DOMAIN,
        identifier="/media",
        title="Local Media",
        media_class=MediaClass.DIRECTORY,
        media_content_type="listing",
        can_play=False,
        can_expand=True,
    )

    with patch(
        "homeassistant.components.media_source.http.async_browse_media",
        return_value=media,
    ):
        await client.send_json(
            {
                "id": 1,
                "type": "media_source/browse_media",
            }
        )

        msg = await client.receive_json()

    assert msg["success"]
    assert msg["id"] == 1
    assert media.as_dict() == msg["result"]

    with patch(
        "homeassistant.components.media_source.http.async_browse_media",
        side_effect=BrowseError("test"),
    ):
        await client.send_json(
            {
                "id": 2,
                "type": "media_source/browse_media",
                "media_content_id": "invalid",
            }
        )

        msg = await client.receive_json()

    assert not msg["success"]
    assert msg["error"]["code"] == "browse_media_failed"
    assert msg["error"]["message"] == "test"