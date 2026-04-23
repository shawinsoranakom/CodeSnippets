async def test_lovelace_dashboard_deleted_re_registers_panel(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    hass_storage: dict[str, Any],
) -> None:
    """Test deleting the lovelace dashboard re-registers the default panel."""
    # Pre-populate storage with existing lovelace config (triggers migration)
    hass_storage[dashboard.CONFIG_STORAGE_KEY_DEFAULT] = {
        "version": 1,
        "key": dashboard.CONFIG_STORAGE_KEY_DEFAULT,
        "data": {"config": {"views": [{"title": "Home"}]}},
    }

    assert await async_setup_component(hass, "lovelace", {})

    # After migration, lovelace panel should be registered as a dashboard
    assert "lovelace" in hass.data[frontend.DATA_PANELS]

    client = await hass_ws_client(hass)

    # Dashboard should be in the list
    await client.send_json({"id": 5, "type": "lovelace/dashboards/list"})
    response = await client.receive_json()
    assert response["success"]
    assert len(response["result"]) == 1
    dashboard_id = response["result"][0]["id"]

    # Delete the lovelace dashboard
    await client.send_json(
        {"id": 6, "type": "lovelace/dashboards/delete", "dashboard_id": dashboard_id}
    )
    response = await client.receive_json()
    assert response["success"]

    # Dashboard should be gone from the list
    await client.send_json({"id": 7, "type": "lovelace/dashboards/list"})
    response = await client.receive_json()
    assert response["success"]
    assert response["result"] == []

    # But the lovelace panel should still be registered (re-registered as default)
    assert "lovelace" in hass.data[frontend.DATA_PANELS]