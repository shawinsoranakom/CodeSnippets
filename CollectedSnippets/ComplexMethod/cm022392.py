async def test_get_matching_entries_ws(
    hass: HomeAssistant, hass_ws_client: WebSocketGenerator
) -> None:
    """Test get entries with the websocket api."""
    assert await async_setup_component(hass, "config", {})
    mock_integration(hass, MockModule("comp1"))
    mock_integration(
        hass, MockModule("comp2", partial_manifest={"integration_type": "helper"})
    )
    mock_integration(
        hass, MockModule("comp3", partial_manifest={"integration_type": "hub"})
    )
    mock_integration(
        hass, MockModule("comp4", partial_manifest={"integration_type": "device"})
    )
    mock_integration(
        hass, MockModule("comp5", partial_manifest={"integration_type": "service"})
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
    MockConfigEntry(
        domain="comp4",
        title="Test 4",
        source="bla4",
    ).add_to_hass(hass)
    MockConfigEntry(
        domain="comp5",
        title="Test 5",
        source="bla5",
    ).add_to_hass(hass)

    ws_client = await hass_ws_client(hass)

    await ws_client.send_json_auto_id({"type": "config_entries/get"})
    response = await ws_client.receive_json()
    timestamp = utcnow().timestamp()
    assert response["result"] == [
        {
            "created_at": timestamp,
            "disabled_by": None,
            "domain": "comp1",
            "entry_id": ANY,
            "error_reason_translation_key": None,
            "error_reason_translation_placeholders": None,
            "modified_at": timestamp,
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
        {
            "created_at": timestamp,
            "disabled_by": None,
            "domain": "comp2",
            "entry_id": ANY,
            "error_reason_translation_key": None,
            "error_reason_translation_placeholders": None,
            "modified_at": timestamp,
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
        {
            "created_at": timestamp,
            "disabled_by": "user",
            "domain": "comp3",
            "entry_id": ANY,
            "error_reason_translation_key": None,
            "error_reason_translation_placeholders": None,
            "modified_at": timestamp,
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
        {
            "created_at": timestamp,
            "disabled_by": None,
            "domain": "comp4",
            "entry_id": ANY,
            "error_reason_translation_key": None,
            "error_reason_translation_placeholders": None,
            "modified_at": timestamp,
            "num_subentries": 0,
            "pref_disable_new_entities": False,
            "pref_disable_polling": False,
            "reason": None,
            "source": "bla4",
            "state": "not_loaded",
            "supported_subentry_types": {},
            "supports_options": False,
            "supports_reconfigure": False,
            "supports_remove_device": False,
            "supports_unload": False,
            "title": "Test 4",
        },
        {
            "created_at": timestamp,
            "disabled_by": None,
            "domain": "comp5",
            "entry_id": ANY,
            "error_reason_translation_key": None,
            "error_reason_translation_placeholders": None,
            "modified_at": timestamp,
            "num_subentries": 0,
            "pref_disable_new_entities": False,
            "pref_disable_polling": False,
            "reason": None,
            "source": "bla5",
            "state": "not_loaded",
            "supported_subentry_types": {},
            "supports_options": False,
            "supports_reconfigure": False,
            "supports_remove_device": False,
            "supports_unload": False,
            "title": "Test 5",
        },
    ]

    await ws_client.send_json_auto_id(
        {
            "type": "config_entries/get",
            "domain": "comp1",
            "type_filter": "hub",
        }
    )
    response = await ws_client.receive_json()
    assert response["result"] == [
        {
            "created_at": timestamp,
            "disabled_by": None,
            "domain": "comp1",
            "entry_id": ANY,
            "error_reason_translation_key": None,
            "error_reason_translation_placeholders": None,
            "modified_at": timestamp,
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
        }
    ]

    await ws_client.send_json_auto_id(
        {
            "type": "config_entries/get",
            "type_filter": ["service", "device"],
        }
    )
    response = await ws_client.receive_json()
    assert response["result"] == [
        {
            "created_at": timestamp,
            "disabled_by": None,
            "domain": "comp4",
            "entry_id": ANY,
            "error_reason_translation_key": None,
            "error_reason_translation_placeholders": None,
            "modified_at": timestamp,
            "num_subentries": 0,
            "pref_disable_new_entities": False,
            "pref_disable_polling": False,
            "reason": None,
            "source": "bla4",
            "state": "not_loaded",
            "supported_subentry_types": {},
            "supports_options": False,
            "supports_reconfigure": False,
            "supports_remove_device": False,
            "supports_unload": False,
            "title": "Test 4",
        },
        {
            "created_at": timestamp,
            "disabled_by": None,
            "domain": "comp5",
            "entry_id": ANY,
            "error_reason_translation_key": None,
            "error_reason_translation_placeholders": None,
            "modified_at": timestamp,
            "num_subentries": 0,
            "pref_disable_new_entities": False,
            "pref_disable_polling": False,
            "reason": None,
            "source": "bla5",
            "state": "not_loaded",
            "supported_subentry_types": {},
            "supports_options": False,
            "supports_reconfigure": False,
            "supports_remove_device": False,
            "supports_unload": False,
            "title": "Test 5",
        },
    ]

    await ws_client.send_json_auto_id(
        {
            "type": "config_entries/get",
            "type_filter": "hub",
        }
    )
    response = await ws_client.receive_json()
    assert response["result"] == [
        {
            "created_at": timestamp,
            "disabled_by": None,
            "domain": "comp1",
            "entry_id": ANY,
            "error_reason_translation_key": None,
            "error_reason_translation_placeholders": None,
            "modified_at": timestamp,
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
        {
            "created_at": timestamp,
            "disabled_by": "user",
            "domain": "comp3",
            "entry_id": ANY,
            "error_reason_translation_key": None,
            "error_reason_translation_placeholders": None,
            "modified_at": timestamp,
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
    ]

    # Verify we skip broken integrations
    with patch(
        "homeassistant.components.config.config_entries.async_get_integrations",
        return_value={"any": IntegrationNotFound("any")},
    ):
        await ws_client.send_json_auto_id(
            {
                "type": "config_entries/get",
                "type_filter": "hub",
            }
        )
        response = await ws_client.receive_json()

    assert response["result"] == [
        {
            "created_at": timestamp,
            "disabled_by": None,
            "domain": "comp1",
            "entry_id": ANY,
            "error_reason_translation_key": None,
            "error_reason_translation_placeholders": None,
            "modified_at": timestamp,
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
        {
            "created_at": timestamp,
            "disabled_by": None,
            "domain": "comp2",
            "entry_id": ANY,
            "error_reason_translation_key": None,
            "error_reason_translation_placeholders": None,
            "modified_at": timestamp,
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
        {
            "created_at": timestamp,
            "disabled_by": "user",
            "domain": "comp3",
            "entry_id": ANY,
            "error_reason_translation_key": None,
            "error_reason_translation_placeholders": None,
            "modified_at": timestamp,
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
        {
            "created_at": timestamp,
            "disabled_by": None,
            "domain": "comp4",
            "entry_id": ANY,
            "error_reason_translation_key": None,
            "error_reason_translation_placeholders": None,
            "modified_at": timestamp,
            "num_subentries": 0,
            "pref_disable_new_entities": False,
            "pref_disable_polling": False,
            "reason": None,
            "source": "bla4",
            "state": "not_loaded",
            "supported_subentry_types": {},
            "supports_options": False,
            "supports_reconfigure": False,
            "supports_remove_device": False,
            "supports_unload": False,
            "title": "Test 4",
        },
        {
            "created_at": timestamp,
            "disabled_by": None,
            "domain": "comp5",
            "entry_id": ANY,
            "error_reason_translation_key": None,
            "error_reason_translation_placeholders": None,
            "modified_at": timestamp,
            "num_subentries": 0,
            "pref_disable_new_entities": False,
            "pref_disable_polling": False,
            "reason": None,
            "source": "bla5",
            "state": "not_loaded",
            "supported_subentry_types": {},
            "supports_options": False,
            "supports_reconfigure": False,
            "supports_remove_device": False,
            "supports_unload": False,
            "title": "Test 5",
        },
    ]

    # Verify we don't send config entries when only helpers are requested
    with patch(
        "homeassistant.components.config.config_entries.async_get_integrations",
        return_value={"any": IntegrationNotFound("any")},
    ):
        await ws_client.send_json_auto_id(
            {
                "type": "config_entries/get",
                "type_filter": ["helper"],
            }
        )
        response = await ws_client.receive_json()

    assert response["result"] == []

    # Verify we raise if something really goes wrong

    with patch(
        "homeassistant.components.config.config_entries.async_get_integrations",
        return_value={"any": Exception()},
    ):
        await ws_client.send_json_auto_id(
            {
                "type": "config_entries/get",
                "type_filter": ["device", "hub", "service"],
            }
        )
        response = await ws_client.receive_json()

    assert response["success"] is False