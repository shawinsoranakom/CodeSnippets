async def test_extraction_functions_with_trigger_targets(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    hass_ws_client: WebSocketGenerator,
) -> None:
    """Test extraction functions with targets in triggers.

    This test verifies that targets specified in trigger configurations
    (using new-style triggers that support target) are properly extracted for
    entity, device, area, floor, and label references.
    """
    config_entry = MockConfigEntry(domain="fake_integration", data={})
    config_entry.mock_state(hass, ConfigEntryState.LOADED)
    config_entry.add_to_hass(hass)

    trigger_device = device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        connections={(dr.CONNECTION_NETWORK_MAC, "00:00:00:00:00:01")},
    )

    await async_setup_component(hass, "homeassistant", {})
    await async_setup_component(
        hass, "scene", {"scene": {"name": "test", "entities": {}}}
    )
    await hass.async_block_till_done()

    # Enable the new_triggers_conditions feature flag to allow new-style triggers
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
                        # Single entity_id in target
                        {
                            "trigger": "scene.activated",
                            "target": {"entity_id": "scene.target_entity"},
                        },
                        # Multiple entity_ids in target
                        {
                            "trigger": "scene.activated",
                            "target": {
                                "entity_id": [
                                    "scene.target_entity_list1",
                                    "scene.target_entity_list2",
                                ]
                            },
                        },
                        # Single device_id in target
                        {
                            "trigger": "scene.activated",
                            "target": {"device_id": trigger_device.id},
                        },
                        # Multiple device_ids in target
                        {
                            "trigger": "scene.activated",
                            "target": {
                                "device_id": [
                                    "target-device-1",
                                    "target-device-2",
                                ]
                            },
                        },
                        # Single area_id in target
                        {
                            "trigger": "scene.activated",
                            "target": {"area_id": "area-target-single"},
                        },
                        # Multiple area_ids in target
                        {
                            "trigger": "scene.activated",
                            "target": {"area_id": ["area-target-1", "area-target-2"]},
                        },
                        # Single floor_id in target
                        {
                            "trigger": "scene.activated",
                            "target": {"floor_id": "floor-target-single"},
                        },
                        # Multiple floor_ids in target
                        {
                            "trigger": "scene.activated",
                            "target": {
                                "floor_id": ["floor-target-1", "floor-target-2"]
                            },
                        },
                        # Single label_id in target
                        {
                            "trigger": "scene.activated",
                            "target": {"label_id": "label-target-single"},
                        },
                        # Multiple label_ids in target
                        {
                            "trigger": "scene.activated",
                            "target": {
                                "label_id": ["label-target-1", "label-target-2"]
                            },
                        },
                        # Combined targets
                        {
                            "trigger": "scene.activated",
                            "target": {
                                "entity_id": "scene.combined_entity",
                                "device_id": "combined-device",
                                "area_id": "combined-area",
                                "floor_id": "combined-floor",
                                "label_id": "combined-label",
                            },
                        },
                    ],
                    "conditions": [],
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

    # Test entity extraction from trigger targets
    assert set(automation.entities_in_automation(hass, "automation.test1")) == {
        "scene.target_entity",
        "scene.target_entity_list1",
        "scene.target_entity_list2",
        "scene.combined_entity",
        "light.action_entity",
    }

    # Test device extraction from trigger targets
    assert set(automation.devices_in_automation(hass, "automation.test1")) == {
        trigger_device.id,
        "target-device-1",
        "target-device-2",
        "combined-device",
    }

    # Test area extraction from trigger targets
    assert set(automation.areas_in_automation(hass, "automation.test1")) == {
        "area-target-single",
        "area-target-1",
        "area-target-2",
        "combined-area",
    }

    # Test floor extraction from trigger targets
    assert set(automation.floors_in_automation(hass, "automation.test1")) == {
        "floor-target-single",
        "floor-target-1",
        "floor-target-2",
        "combined-floor",
    }

    # Test label extraction from trigger targets
    assert set(automation.labels_in_automation(hass, "automation.test1")) == {
        "label-target-single",
        "label-target-1",
        "label-target-2",
        "combined-label",
    }

    # Test automations_with_* functions
    assert set(automation.automations_with_entity(hass, "scene.target_entity")) == {
        "automation.test1"
    }
    assert set(automation.automations_with_device(hass, trigger_device.id)) == {
        "automation.test1"
    }
    assert set(automation.automations_with_area(hass, "area-target-single")) == {
        "automation.test1"
    }
    assert set(automation.automations_with_floor(hass, "floor-target-single")) == {
        "automation.test1"
    }
    assert set(automation.automations_with_label(hass, "label-target-single")) == {
        "automation.test1"
    }