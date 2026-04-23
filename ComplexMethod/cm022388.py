async def test_get_single(
    hass: HomeAssistant, hass_ws_client: WebSocketGenerator
) -> None:
    """Test that we can get a config entry."""
    assert await async_setup_component(hass, "config", {})
    ws_client = await hass_ws_client(hass)

    entry = MockConfigEntry(domain="test", state=core_ce.ConfigEntryState.LOADED)
    entry.add_to_hass(hass)

    assert entry.pref_disable_new_entities is False
    assert entry.pref_disable_polling is False

    await ws_client.send_json_auto_id(
        {
            "type": "config_entries/get_single",
            "entry_id": entry.entry_id,
        }
    )
    response = await ws_client.receive_json()

    timestamp = utcnow().timestamp()
    assert response["success"]
    assert response["result"]["config_entry"] == {
        "created_at": timestamp,
        "disabled_by": None,
        "domain": "test",
        "entry_id": entry.entry_id,
        "error_reason_translation_key": None,
        "error_reason_translation_placeholders": None,
        "modified_at": timestamp,
        "num_subentries": 0,
        "pref_disable_new_entities": False,
        "pref_disable_polling": False,
        "reason": None,
        "source": "user",
        "state": "loaded",
        "supported_subentry_types": {},
        "supports_options": False,
        "supports_reconfigure": False,
        "supports_remove_device": False,
        "supports_unload": False,
        "title": "Mock Title",
    }

    await ws_client.send_json_auto_id(
        {
            "type": "config_entries/get_single",
            "entry_id": "blah",
        }
    )
    response = await ws_client.receive_json()
    assert not response["success"]
    assert response["error"] == {
        "code": "not_found",
        "message": "Config entry not found",
    }