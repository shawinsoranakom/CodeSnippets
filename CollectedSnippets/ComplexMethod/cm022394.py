async def test_subscribe_entries_ws_filtered(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    freezer: FrozenDateTimeFactory,
) -> None:
    """Test subscribe entries with the websocket api with a type filter."""
    created = utcnow().timestamp()
    assert await async_setup_component(hass, "config", {})
    mock_integration(hass, MockModule("comp1"))
    mock_integration(
        hass, MockModule("comp2", partial_manifest={"integration_type": "helper"})
    )
    mock_integration(
        hass, MockModule("comp3", partial_manifest={"integration_type": "device"})
    )
    mock_integration(
        hass, MockModule("comp4", partial_manifest={"integration_type": "service"})
    )
    entry = MockConfigEntry(
        domain="comp1",
        title="Test 1",
        source="bla",
    )
    entry.add_to_hass(hass)
    entry2 = MockConfigEntry(
        domain="comp2",
        title="Test 2",
        source="bla2",
        state=core_ce.ConfigEntryState.SETUP_ERROR,
        reason="Unsupported API",
    )
    entry2.add_to_hass(hass)
    entry3 = MockConfigEntry(
        domain="comp3",
        title="Test 3",
        source="bla3",
        disabled_by=core_ce.ConfigEntryDisabler.USER,
    )
    entry3.add_to_hass(hass)
    entry4 = MockConfigEntry(
        domain="comp4",
        title="Test 4",
        source="bla4",
    )
    entry4.add_to_hass(hass)

    ws_client = await hass_ws_client(hass)

    await ws_client.send_json(
        {
            "id": 5,
            "type": "config_entries/subscribe",
            "type_filter": ["hub", "device"],
        }
    )
    response = await ws_client.receive_json()
    assert response["id"] == 5
    assert response["result"] is None
    assert response["success"] is True
    assert response["type"] == "result"
    response = await ws_client.receive_json()
    assert response["id"] == 5
    assert response["event"] == [
        {
            "type": None,
            "entry": {
                "created_at": created,
                "disabled_by": None,
                "domain": "comp1",
                "entry_id": ANY,
                "error_reason_translation_key": None,
                "error_reason_translation_placeholders": None,
                "modified_at": created,
                "num_subentries": 0,
                "pref_disable_new_entities": False,
                "pref_disable_polling": False,
                "reason": None,
                "source": "bla",
                "state": "not_loaded",
                "supported_subentry_types": {},
                "supports_options": False,
                "supports_reconfigure": False,
                "supports_remove_device": False,
                "supports_unload": False,
                "title": "Test 1",
            },
        },
        {
            "type": None,
            "entry": {
                "created_at": created,
                "disabled_by": "user",
                "domain": "comp3",
                "entry_id": ANY,
                "error_reason_translation_key": None,
                "error_reason_translation_placeholders": None,
                "modified_at": created,
                "num_subentries": 0,
                "pref_disable_new_entities": False,
                "pref_disable_polling": False,
                "reason": None,
                "source": "bla3",
                "state": "not_loaded",
                "supported_subentry_types": {},
                "supports_options": False,
                "supports_reconfigure": False,
                "supports_remove_device": False,
                "supports_unload": False,
                "title": "Test 3",
            },
        },
    ]
    freezer.tick()
    modified = utcnow().timestamp()
    assert hass.config_entries.async_update_entry(entry, title="changed")
    assert hass.config_entries.async_update_entry(entry3, title="changed too")
    assert hass.config_entries.async_update_entry(entry4, title="changed but ignored")
    response = await ws_client.receive_json()
    assert response["id"] == 5
    assert response["event"] == [
        {
            "entry": {
                "created_at": created,
                "disabled_by": None,
                "domain": "comp1",
                "entry_id": ANY,
                "error_reason_translation_key": None,
                "error_reason_translation_placeholders": None,
                "modified_at": modified,
                "num_subentries": 0,
                "pref_disable_new_entities": False,
                "pref_disable_polling": False,
                "reason": None,
                "source": "bla",
                "state": "not_loaded",
                "supported_subentry_types": {},
                "supports_options": False,
                "supports_reconfigure": False,
                "supports_remove_device": False,
                "supports_unload": False,
                "title": "changed",
            },
            "type": "updated",
        }
    ]
    response = await ws_client.receive_json()
    assert response["id"] == 5
    assert response["event"] == [
        {
            "entry": {
                "created_at": created,
                "disabled_by": "user",
                "domain": "comp3",
                "entry_id": ANY,
                "error_reason_translation_key": None,
                "error_reason_translation_placeholders": None,
                "modified_at": modified,
                "num_subentries": 0,
                "pref_disable_new_entities": False,
                "pref_disable_polling": False,
                "reason": None,
                "source": "bla3",
                "state": "not_loaded",
                "supported_subentry_types": {},
                "supports_options": False,
                "supports_reconfigure": False,
                "supports_remove_device": False,
                "supports_unload": False,
                "title": "changed too",
            },
            "type": "updated",
        }
    ]
    freezer.tick()
    modified = utcnow().timestamp()
    await hass.config_entries.async_remove(entry.entry_id)
    await hass.config_entries.async_remove(entry2.entry_id)
    response = await ws_client.receive_json()
    assert response["id"] == 5
    assert response["event"] == [
        {
            "entry": {
                "created_at": created,
                "disabled_by": None,
                "domain": "comp1",
                "entry_id": ANY,
                "error_reason_translation_key": None,
                "error_reason_translation_placeholders": None,
                "modified_at": modified,
                "num_subentries": 0,
                "pref_disable_new_entities": False,
                "pref_disable_polling": False,
                "reason": None,
                "source": "bla",
                "state": "not_loaded",
                "supported_subentry_types": {},
                "supports_options": False,
                "supports_reconfigure": False,
                "supports_remove_device": False,
                "supports_unload": False,
                "title": "changed",
            },
            "type": "removed",
        }
    ]
    freezer.tick()
    await hass.config_entries.async_add(entry)
    response = await ws_client.receive_json()
    assert response["id"] == 5
    assert response["event"] == [
        {
            "entry": {
                "created_at": entry.created_at.timestamp(),
                "disabled_by": None,
                "domain": "comp1",
                "entry_id": ANY,
                "error_reason_translation_key": None,
                "error_reason_translation_placeholders": None,
                "modified_at": entry.modified_at.timestamp(),
                "num_subentries": 0,
                "pref_disable_new_entities": False,
                "pref_disable_polling": False,
                "reason": None,
                "source": "bla",
                "state": "not_loaded",
                "supported_subentry_types": {},
                "supports_options": False,
                "supports_reconfigure": False,
                "supports_remove_device": False,
                "supports_unload": False,
                "title": "changed",
            },
            "type": "added",
        }
    ]