async def test_update_subentry(
    hass: HomeAssistant, hass_ws_client: WebSocketGenerator
) -> None:
    """Test that we can update a subentry."""
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
                unique_id="mock_unique_id",
            )
        ],
    )
    entry.add_to_hass(hass)

    await ws_client.send_json_auto_id(
        {
            "type": "config_entries/subentries/update",
            "entry_id": entry.entry_id,
            "subentry_id": "mock_id",
            "title": "Updated Title",
        }
    )
    response = await ws_client.receive_json()

    assert response["success"]
    assert response["result"] is None

    assert list(entry.subentries.values())[0].title == "Updated Title"
    assert list(entry.subentries.values())[0].unique_id == "mock_unique_id"
    assert list(entry.subentries.values())[0].data["test"] == "test"

    # Try renaming subentry from an unknown entry
    ws_client = await hass_ws_client(hass)
    await ws_client.send_json_auto_id(
        {
            "type": "config_entries/subentries/update",
            "entry_id": "no_such_entry",
            "subentry_id": "mock_id",
            "title": "Updated Title",
        }
    )
    response = await ws_client.receive_json()

    assert not response["success"]
    assert response["error"] == {
        "code": "not_found",
        "message": "Config entry not found",
    }

    # Try renaming subentry from an unknown subentry
    ws_client = await hass_ws_client(hass)
    await ws_client.send_json_auto_id(
        {
            "type": "config_entries/subentries/update",
            "entry_id": entry.entry_id,
            "subentry_id": "no_such_entry2",
            "title": "Updated Title2",
        }
    )
    response = await ws_client.receive_json()

    assert not response["success"]
    assert response["error"] == {
        "code": "not_found",
        "message": "Config subentry not found",
    }