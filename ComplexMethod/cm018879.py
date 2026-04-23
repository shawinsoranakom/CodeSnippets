async def test_websocket_resolve_media(
    hass: HomeAssistant, hass_ws_client: WebSocketGenerator, filename
) -> None:
    """Test browse media websocket."""
    assert await async_setup_component(hass, media_source.DOMAIN, {})
    await hass.async_block_till_done()

    client = await hass_ws_client(hass)

    media = media_source.models.PlayMedia(
        f"/media/local/{filename}",
        "audio/mpeg",
    )

    with patch(
        "homeassistant.components.media_source.http.async_resolve_media",
        return_value=media,
    ):
        await client.send_json(
            {
                "id": 1,
                "type": "media_source/resolve_media",
                "media_content_id": f"{const.URI_SCHEME}{media_source.DOMAIN}/local/{filename}",
            }
        )

        msg = await client.receive_json()

    assert msg["success"]
    assert msg["id"] == 1
    assert msg["result"]["mime_type"] == media.mime_type

    # Validate url is relative and signed.
    assert msg["result"]["url"][0] == "/"
    parsed = yarl.URL(msg["result"]["url"])
    assert parsed.path == media.url
    assert "authSig" in parsed.query

    with patch(
        "homeassistant.components.media_source.http.async_resolve_media",
        side_effect=media_source.Unresolvable("test"),
    ):
        await client.send_json(
            {
                "id": 2,
                "type": "media_source/resolve_media",
                "media_content_id": "invalid",
            }
        )

        msg = await client.receive_json()

    assert not msg["success"]
    assert msg["error"]["code"] == "resolve_media_failed"
    assert msg["error"]["message"] == "test"