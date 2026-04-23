async def test_delete_subentry(
    hass: HomeAssistant, hass_ws_client: WebSocketGenerator
) -> None:
    """Test that we can delete a subentry."""
    assert await async_setup_component(hass, "config", {})
    ws_client = await hass_ws_client(hass)

    entry = MockConfigEntry(
        domain="test",
        state=core_ce.ConfigEntryState.LOADED,
        subentries_data=[
            core_ce.ConfigSubentryData(
                data={"test": "test"},
                subentry_id="mock_id",
                subentry_type="test",
                title="Mock title",
            )
        ],
    )
    entry.add_to_hass(hass)

    assert entry.pref_disable_new_entities is False
    assert entry.pref_disable_polling is False

    await ws_client.send_json_auto_id(
        {
            "type": "config_entries/subentries/delete",
            "entry_id": entry.entry_id,
            "subentry_id": "mock_id",
        }
    )
    response = await ws_client.receive_json()

    assert response["success"]
    assert response["result"] is None

    await ws_client.send_json_auto_id(
        {
            "type": "config_entries/subentries/list",
            "entry_id": entry.entry_id,
        }
    )
    response = await ws_client.receive_json()

    assert response["success"]
    assert response["result"] == []

    # Try deleting the subentry again
    await ws_client.send_json_auto_id(
        {
            "type": "config_entries/subentries/delete",
            "entry_id": entry.entry_id,
            "subentry_id": "mock_id",
        }
    )
    response = await ws_client.receive_json()

    assert not response["success"]
    assert response["error"] == {
        "code": "not_found",
        "message": "Config subentry not found",
    }

    # Try deleting subentry from an unknown entry
    await ws_client.send_json_auto_id(
        {
            "type": "config_entries/subentries/delete",
            "entry_id": "no_such_entry",
            "subentry_id": "mock_id",
        }
    )
    response = await ws_client.receive_json()

    assert not response["success"]
    assert response["error"] == {
        "code": "not_found",
        "message": "Config entry not found",
    }