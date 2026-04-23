async def test_lovelace_from_storage_migration(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    hass_storage: dict[str, Any],
) -> None:
    """Test we migrate existing lovelace config from storage to dashboard."""
    # Pre-populate storage with existing lovelace config
    hass_storage[dashboard.CONFIG_STORAGE_KEY_DEFAULT] = {
        "version": 1,
        "key": dashboard.CONFIG_STORAGE_KEY_DEFAULT,
        "data": {"config": {"views": [{"title": "Home"}]}},
    }

    assert await async_setup_component(hass, "lovelace", {})

    # After migration, lovelace panel should be registered as a dashboard
    assert "lovelace" in hass.data[frontend.DATA_PANELS]
    assert hass.data[frontend.DATA_PANELS]["lovelace"].config == {"mode": "storage"}

    client = await hass_ws_client(hass)

    # Dashboard should be in the list
    await client.send_json({"id": 5, "type": "lovelace/dashboards/list"})
    response = await client.receive_json()
    assert response["success"]
    assert len(response["result"]) == 1
    assert response["result"][0]["url_path"] == "lovelace"
    assert response["result"][0]["title"] == "Overview"

    # Fetch migrated config
    await client.send_json({"id": 6, "type": "lovelace/config", "url_path": "lovelace"})
    response = await client.receive_json()
    assert response["success"]
    assert response["result"] == {"views": [{"title": "Home"}]}

    # Old storage key should be gone, new one should exist
    assert dashboard.CONFIG_STORAGE_KEY_DEFAULT not in hass_storage
    assert dashboard.CONFIG_STORAGE_KEY.format("lovelace") in hass_storage

    # Store new config
    events = async_capture_events(hass, const.EVENT_LOVELACE_UPDATED)

    await client.send_json(
        {
            "id": 7,
            "type": "lovelace/config/save",
            "url_path": "lovelace",
            "config": {"yo": "hello"},
        }
    )
    response = await client.receive_json()
    assert response["success"]
    assert hass_storage[dashboard.CONFIG_STORAGE_KEY.format("lovelace")]["data"] == {
        "config": {"yo": "hello"}
    }
    assert len(events) == 1

    # Load new config
    await client.send_json({"id": 8, "type": "lovelace/config", "url_path": "lovelace"})
    response = await client.receive_json()
    assert response["success"]
    assert response["result"] == {"yo": "hello"}

    # Test with recovery mode
    hass.config.recovery_mode = True
    await client.send_json({"id": 9, "type": "lovelace/config", "url_path": "lovelace"})
    response = await client.receive_json()
    assert not response["success"]
    assert response["error"]["code"] == "config_not_found"

    await client.send_json(
        {
            "id": 10,
            "type": "lovelace/config/save",
            "url_path": "lovelace",
            "config": {"yo": "hello"},
        }
    )
    response = await client.receive_json()
    assert not response["success"]

    await client.send_json(
        {"id": 11, "type": "lovelace/config/delete", "url_path": "lovelace"}
    )
    response = await client.receive_json()
    assert not response["success"]