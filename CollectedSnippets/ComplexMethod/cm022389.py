async def test_update_prefrences(
    hass: HomeAssistant, hass_ws_client: WebSocketGenerator
) -> None:
    """Test that we can update system options."""
    assert await async_setup_component(hass, "config", {})
    ws_client = await hass_ws_client(hass)

    entry = MockConfigEntry(domain="test", state=core_ce.ConfigEntryState.LOADED)
    entry.add_to_hass(hass)
    hass.config.components.add("test")

    assert entry.pref_disable_new_entities is False
    assert entry.pref_disable_polling is False

    await ws_client.send_json(
        {
            "id": 6,
            "type": "config_entries/update",
            "entry_id": entry.entry_id,
            "pref_disable_new_entities": True,
        }
    )
    response = await ws_client.receive_json()

    assert response["success"]
    assert response["result"]["require_restart"] is False
    assert response["result"]["config_entry"]["pref_disable_new_entities"] is True
    assert response["result"]["config_entry"]["pref_disable_polling"] is False

    assert entry.pref_disable_new_entities is True
    assert entry.pref_disable_polling is False

    await ws_client.send_json(
        {
            "id": 7,
            "type": "config_entries/update",
            "entry_id": entry.entry_id,
            "pref_disable_new_entities": False,
            "pref_disable_polling": True,
        }
    )
    response = await ws_client.receive_json()

    assert response["success"]
    assert response["result"]["require_restart"] is True
    assert response["result"]["config_entry"]["pref_disable_new_entities"] is False
    assert response["result"]["config_entry"]["pref_disable_polling"] is True

    assert entry.pref_disable_new_entities is False
    assert entry.pref_disable_polling is True