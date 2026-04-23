async def test_get_entries(hass: HomeAssistant, client: TestClient) -> None:
    """Test get entries."""
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

    config_entry_flow.register_discovery_flow("comp2", "Comp 2", lambda: None)

    entry = MockConfigEntry(
        domain="comp1",
        title="Test 1",
        source="bla",
    )
    entry.supports_unload = True
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

    resp = await client.get("/api/config/config_entries/entry")
    assert resp.status == HTTPStatus.OK
    data = await resp.json()
    for entry in data:
        entry.pop("entry_id")
    timestamp = utcnow().timestamp()
    assert data == [
        {
            "created_at": timestamp,
            "disabled_by": None,
            "domain": "comp1",
            "error_reason_translation_key": None,
            "error_reason_translation_placeholders": None,
            "modified_at": timestamp,
            "num_subentries": 0,
            "pref_disable_new_entities": False,
            "pref_disable_polling": False,
            "reason": None,
            "source": "bla",
            "state": core_ce.ConfigEntryState.NOT_LOADED.value,
            "supported_subentry_types": {},
            "supports_options": True,
            "supports_reconfigure": False,
            "supports_remove_device": False,
            "supports_unload": True,
            "title": "Test 1",
        },
        {
            "created_at": timestamp,
            "disabled_by": None,
            "domain": "comp2",
            "error_reason_translation_key": None,
            "error_reason_translation_placeholders": None,
            "modified_at": timestamp,
            "num_subentries": 0,
            "pref_disable_new_entities": False,
            "pref_disable_polling": False,
            "reason": "Unsupported API",
            "source": "bla2",
            "state": core_ce.ConfigEntryState.SETUP_ERROR.value,
            "supported_subentry_types": {},
            "supports_options": False,
            "supports_reconfigure": False,
            "supports_remove_device": False,
            "supports_unload": False,
            "title": "Test 2",
        },
        {
            "created_at": timestamp,
            "disabled_by": core_ce.ConfigEntryDisabler.USER,
            "domain": "comp3",
            "error_reason_translation_key": None,
            "error_reason_translation_placeholders": None,
            "modified_at": timestamp,
            "num_subentries": 0,
            "pref_disable_new_entities": False,
            "pref_disable_polling": False,
            "reason": None,
            "source": "bla3",
            "state": core_ce.ConfigEntryState.NOT_LOADED.value,
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
            "error_reason_translation_key": None,
            "error_reason_translation_placeholders": None,
            "modified_at": timestamp,
            "num_subentries": 0,
            "pref_disable_new_entities": False,
            "pref_disable_polling": False,
            "reason": None,
            "source": "bla4",
            "state": core_ce.ConfigEntryState.NOT_LOADED.value,
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
            "error_reason_translation_key": None,
            "error_reason_translation_placeholders": None,
            "modified_at": timestamp,
            "num_subentries": 0,
            "pref_disable_new_entities": False,
            "pref_disable_polling": False,
            "reason": None,
            "source": "bla5",
            "state": core_ce.ConfigEntryState.NOT_LOADED.value,
            "supported_subentry_types": {},
            "supports_options": False,
            "supports_reconfigure": False,
            "supports_remove_device": False,
            "supports_unload": False,
            "title": "Test 5",
        },
    ]

    resp = await client.get("/api/config/config_entries/entry?domain=comp3")
    assert resp.status == HTTPStatus.OK
    data = await resp.json()
    assert len(data) == 1
    assert data[0]["domain"] == "comp3"

    resp = await client.get("/api/config/config_entries/entry?domain=comp3&type=helper")
    assert resp.status == HTTPStatus.OK
    data = await resp.json()
    assert len(data) == 0

    resp = await client.get("/api/config/config_entries/entry?type=hub")
    assert resp.status == HTTPStatus.OK
    data = await resp.json()
    assert len(data) == 2
    assert data[0]["domain"] == "comp1"
    assert data[1]["domain"] == "comp3"

    resp = await client.get("/api/config/config_entries/entry?type=device")
    assert resp.status == HTTPStatus.OK
    data = await resp.json()
    assert len(data) == 1
    assert data[0]["domain"] == "comp4"

    resp = await client.get("/api/config/config_entries/entry?type=service")
    assert resp.status == HTTPStatus.OK
    data = await resp.json()
    assert len(data) == 1
    assert data[0]["domain"] == "comp5"