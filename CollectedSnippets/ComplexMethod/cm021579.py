async def test_extraction_functions_with_condition_targets(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    hass_ws_client: WebSocketGenerator,
) -> None:
    """Test extraction functions with targets in conditions."""
    config_entry = MockConfigEntry(domain="fake_integration", data={})
    config_entry.mock_state(hass, ConfigEntryState.LOADED)
    config_entry.add_to_hass(hass)

    condition_device = device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        connections={(dr.CONNECTION_NETWORK_MAC, "00:00:00:00:00:02")},
    )

    await async_setup_component(hass, "homeassistant", {})
    await async_setup_component(hass, "light", {"light": {"platform": "demo"}})
    await hass.async_block_till_done()

    # Enable the new_triggers_conditions feature flag to allow new-style conditions
    assert await async_setup_component(hass, "labs", {})
    ws_client = await hass_ws_client(hass)
    await ws_client.send_json_auto_id(
        {
            "type": "labs/update",
            "domain": "automation",
            "preview_feature": "new_triggers_conditions",
            "enabled": True,
        }
    )
    msg = await ws_client.receive_json()
    assert msg["success"]
    await hass.async_block_till_done()

    assert await async_setup_component(
        hass,
        DOMAIN,
        {
            DOMAIN: [
                {
                    "alias": "test1",
                    "triggers": [
                        {"trigger": "state", "entity_id": "sensor.trigger_state"},
                    ],
                    "conditions": [
                        # Single entity_id in target
                        {
                            "condition": "light.is_on",
                            "target": {"entity_id": "light.condition_entity"},
                            "options": {"behavior": "any"},
                        },
                        # Multiple entity_ids in target
                        {
                            "condition": "light.is_on",
                            "target": {
                                "entity_id": [
                                    "light.condition_entity_list1",
                                    "light.condition_entity_list2",
                                ]
                            },
                            "options": {"behavior": "any"},
                        },
                        # Single device_id in target
                        {
                            "condition": "light.is_on",
                            "target": {"device_id": condition_device.id},
                            "options": {"behavior": "any"},
                        },
                        # Multiple device_ids in target
                        {
                            "condition": "light.is_on",
                            "target": {
                                "device_id": [
                                    "target-device-1",
                                    "target-device-2",
                                ]
                            },
                            "options": {"behavior": "any"},
                        },
                        # Single area_id in target
                        {
                            "condition": "light.is_on",
                            "target": {"area_id": "area-condition-single"},
                            "options": {"behavior": "any"},
                        },
                        # Multiple area_ids in target
                        {
                            "condition": "light.is_on",
                            "target": {
                                "area_id": ["area-condition-1", "area-condition-2"]
                            },
                            "options": {"behavior": "any"},
                        },
                        # Single floor_id in target
                        {
                            "condition": "light.is_on",
                            "target": {"floor_id": "floor-condition-single"},
                            "options": {"behavior": "any"},
                        },
                        # Multiple floor_ids in target
                        {
                            "condition": "light.is_on",
                            "target": {
                                "floor_id": ["floor-condition-1", "floor-condition-2"]
                            },
                            "options": {"behavior": "any"},
                        },
                        # Single label_id in target
                        {
                            "condition": "light.is_on",
                            "target": {"label_id": "label-condition-single"},
                            "options": {"behavior": "any"},
                        },
                        # Multiple label_ids in target
                        {
                            "condition": "light.is_on",
                            "target": {
                                "label_id": ["label-condition-1", "label-condition-2"]
                            },
                            "options": {"behavior": "any"},
                        },
                        # Combined targets
                        {
                            "condition": "light.is_on",
                            "target": {
                                "entity_id": "light.combined_entity",
                                "device_id": "combined-device",
                                "area_id": "combined-area",
                                "floor_id": "combined-floor",
                                "label_id": "combined-label",
                            },
                            "options": {"behavior": "any"},
                        },
                    ],
                    "actions": [
                        {
                            "action": "test.script",
                            "data": {"entity_id": "light.action_entity"},
                        },
                    ],
                },
            ]
        },
    )

    # Test entity extraction from condition targets
    assert set(automation.entities_in_automation(hass, "automation.test1")) == {
        "sensor.trigger_state",
        "light.condition_entity",
        "light.condition_entity_list1",
        "light.condition_entity_list2",
        "light.combined_entity",
        "light.action_entity",
    }

    # Test device extraction from condition targets
    assert set(automation.devices_in_automation(hass, "automation.test1")) == {
        condition_device.id,
        "target-device-1",
        "target-device-2",
        "combined-device",
    }

    # Test area extraction from condition targets
    assert set(automation.areas_in_automation(hass, "automation.test1")) == {
        "area-condition-single",
        "area-condition-1",
        "area-condition-2",
        "combined-area",
    }

    # Test floor extraction from condition targets
    assert set(automation.floors_in_automation(hass, "automation.test1")) == {
        "floor-condition-single",
        "floor-condition-1",
        "floor-condition-2",
        "combined-floor",
    }

    # Test label extraction from condition targets
    assert set(automation.labels_in_automation(hass, "automation.test1")) == {
        "label-condition-single",
        "label-condition-1",
        "label-condition-2",
        "combined-label",
    }

    # Test automations_with_* functions
    assert set(automation.automations_with_entity(hass, "light.condition_entity")) == {
        "automation.test1"
    }
    assert set(automation.automations_with_device(hass, condition_device.id)) == {
        "automation.test1"
    }
    assert set(automation.automations_with_area(hass, "area-condition-single")) == {
        "automation.test1"
    }
    assert set(automation.automations_with_floor(hass, "floor-condition-single")) == {
        "automation.test1"
    }
    assert set(automation.automations_with_label(hass, "label-condition-single")) == {
        "automation.test1"
    }