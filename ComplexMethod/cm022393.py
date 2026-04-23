async def test_subscribe_entries_ws(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    freezer: FrozenDateTimeFactory,
) -> None:
    """Test subscribe entries with the websocket api."""
    assert await async_setup_component(hass, "config", {})
    mock_integration(hass, MockModule("comp1"))
    mock_integration(
        hass, MockModule("comp2", partial_manifest={"integration_type": "helper"})
    )
    mock_integration(
        hass, MockModule("comp3", partial_manifest={"integration_type": "device"})
    )
    entry = MockConfigEntry(
        domain="comp1",
        title="Test 1",
        source="bla",
    )
    entry.add_to_hass(hass)
    MockConfigEntry(
        domain="comp2",
        title="Test 2",
        source="bla2",
        state=core_ce.ConfigEntryState.SETUP_ERROR,
        reason="Unsupported API",
    ).add_to_hass(hass)
    MockConfigEntry(
        domain="comp3",
        title="Test 3",
        source="bla3",
        disabled_by=core_ce.ConfigEntryDisabler.USER,
    ).add_to_hass(hass)

    ws_client = await hass_ws_client(hass)

    await ws_client.send_json(
        {
            "id": 5,
            "type": "config_entries/subscribe",
        }
    )
    response = await ws_client.receive_json()
    assert response["id"] == 5
    assert response["result"] is None
    assert response["success"] is True
    assert response["type"] == "result"
    response = await ws_client.receive_json()
    assert response["id"] == 5
    created = utcnow().timestamp()
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
                "disabled_by": None,
                "domain": "comp2",
                "entry_id": ANY,
                "error_reason_translation_key": None,
                "error_reason_translation_placeholders": None,
                "modified_at": created,
                "num_subentries": 0,
                "pref_disable_new_entities": False,
                "pref_disable_polling": False,
                "reason": "Unsupported API",
                "source": "bla2",
                "state": "setup_error",
                "supported_subentry_types": {},
                "supports_options": False,
                "supports_reconfigure": False,
                "supports_remove_device": False,
                "supports_unload": False,
                "title": "Test 2",
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
    freezer.tick()
    modified = utcnow().timestamp()
    await hass.config_entries.async_remove(entry.entry_id)
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