async def test_browse_media(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    snapshot: SnapshotAssertion,
    hass_ws_client: WebSocketGenerator,
) -> None:
    """Test async_browse_media."""

    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    assert config_entry.state is ConfigEntryState.LOADED

    client = await hass_ws_client()
    await client.send_json_auto_id(
        {
            "type": "media_player/browse_media",
            "entity_id": "media_player.xone",
        }
    )

    response = await client.receive_json()
    assert response["success"]

    assert response["result"] == snapshot(name="library")

    await client.send_json_auto_id(
        {
            "type": "media_player/browse_media",
            "entity_id": "media_player.xone",
            "media_content_id": "App",
            "media_content_type": "app",
        }
    )

    response = await client.receive_json()
    assert response["success"]

    assert response["result"] == snapshot(name="apps")

    await client.send_json_auto_id(
        {
            "type": "media_player/browse_media",
            "entity_id": "media_player.xone",
            "media_content_id": "Game",
            "media_content_type": "game",
        }
    )

    response = await client.receive_json()
    assert response["success"]

    assert response["result"] == snapshot(name="games")