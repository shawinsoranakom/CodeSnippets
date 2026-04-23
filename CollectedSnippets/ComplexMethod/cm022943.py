async def test_extraction_functions(
    hass: HomeAssistant, device_registry: dr.DeviceRegistry
) -> None:
    """Test extraction functions."""
    config_entry = MockConfigEntry(domain="fake_integration", data={})
    config_entry.mock_state(hass, ConfigEntryState.LOADED)
    config_entry.add_to_hass(hass)

    device_in_both = device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        connections={(dr.CONNECTION_NETWORK_MAC, "00:00:00:00:00:02")},
    )
    device_in_last = device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        connections={(dr.CONNECTION_NETWORK_MAC, "00:00:00:00:00:03")},
    )

    assert await async_setup_component(
        hass,
        DOMAIN,
        {
            DOMAIN: {
                "test1": {
                    "sequence": [
                        {
                            "action": "test.script",
                            "data": {"entity_id": "light.in_both"},
                        },
                        {
                            "action": "test.script",
                            "data": {"entity_id": "light.in_first"},
                        },
                        {
                            "entity_id": "light.device_in_both",
                            "domain": "light",
                            "type": "turn_on",
                            "device_id": device_in_both.id,
                        },
                        {
                            "action": "test.test",
                            "target": {"area_id": "area-in-both"},
                        },
                        {
                            "action": "test.test",
                            "target": {"floor_id": "floor-in-both"},
                        },
                        {
                            "action": "test.test",
                            "target": {"label_id": "label-in-both"},
                        },
                    ]
                },
                "test2": {
                    "sequence": [
                        {
                            "action": "test.script",
                            "data": {"entity_id": "light.in_both"},
                        },
                        {
                            "condition": "state",
                            "entity_id": "sensor.condition",
                            "state": "100",
                        },
                        {"scene": "scene.hello"},
                        {
                            "entity_id": "light.device_in_both",
                            "domain": "light",
                            "type": "turn_on",
                            "device_id": device_in_both.id,
                        },
                        {
                            "entity_id": "light.device_in_last",
                            "domain": "light",
                            "type": "turn_on",
                            "device_id": device_in_last.id,
                        },
                    ],
                },
                "test3": {
                    "sequence": [
                        {
                            "action": "test.script",
                            "data": {"entity_id": "light.in_both"},
                        },
                        {
                            "condition": "state",
                            "entity_id": "sensor.condition",
                            "state": "100",
                        },
                        {"scene": "scene.hello"},
                        {
                            "action": "test.test",
                            "target": {"area_id": "area-in-both"},
                        },
                        {
                            "action": "test.test",
                            "target": {"area_id": "area-in-last"},
                        },
                        {
                            "action": "test.test",
                            "target": {"floor_id": "floor-in-both"},
                        },
                        {
                            "action": "test.test",
                            "target": {"floor_id": "floor-in-last"},
                        },
                        {
                            "action": "test.test",
                            "target": {"label_id": "label-in-both"},
                        },
                        {
                            "action": "test.test",
                            "target": {"label_id": "label-in-last"},
                        },
                    ],
                },
            }
        },
    )

    assert set(script.scripts_with_entity(hass, "light.in_both")) == {
        "script.test1",
        "script.test2",
        "script.test3",
    }
    assert set(script.entities_in_script(hass, "script.test1")) == {
        "light.in_both",
        "light.in_first",
    }
    assert set(script.scripts_with_device(hass, device_in_both.id)) == {
        "script.test1",
        "script.test2",
    }
    assert set(script.devices_in_script(hass, "script.test2")) == {
        device_in_both.id,
        device_in_last.id,
    }
    assert set(script.scripts_with_area(hass, "area-in-both")) == {
        "script.test1",
        "script.test3",
    }
    assert set(script.areas_in_script(hass, "script.test3")) == {
        "area-in-both",
        "area-in-last",
    }
    assert set(script.scripts_with_floor(hass, "floor-in-both")) == {
        "script.test1",
        "script.test3",
    }
    assert set(script.floors_in_script(hass, "script.test3")) == {
        "floor-in-both",
        "floor-in-last",
    }
    assert set(script.scripts_with_label(hass, "label-in-both")) == {
        "script.test1",
        "script.test3",
    }
    assert set(script.labels_in_script(hass, "script.test3")) == {
        "label-in-both",
        "label-in-last",
    }
    assert script.blueprint_in_script(hass, "script.test3") is None