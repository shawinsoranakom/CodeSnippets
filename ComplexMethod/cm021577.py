async def test_extraction_functions(
    hass: HomeAssistant, device_registry: dr.DeviceRegistry
) -> None:
    """Test extraction functions."""
    config_entry = MockConfigEntry(domain="fake_integration", data={})
    config_entry.mock_state(hass, ConfigEntryState.LOADED)
    config_entry.add_to_hass(hass)

    condition_device = device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        connections={(dr.CONNECTION_NETWORK_MAC, "00:00:00:00:00:01")},
    )
    device_in_both = device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        connections={(dr.CONNECTION_NETWORK_MAC, "00:00:00:00:00:02")},
    )
    device_in_last = device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        connections={(dr.CONNECTION_NETWORK_MAC, "00:00:00:00:00:03")},
    )
    trigger_device_2 = device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        connections={(dr.CONNECTION_NETWORK_MAC, "00:00:00:00:00:04")},
    )

    await async_setup_component(hass, "homeassistant", {})
    await async_setup_component(hass, "calendar", {"calendar": {"platform": "demo"}})
    # Ensure the calendar entities are setup before attaching triggers
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
                        {
                            "trigger": "numeric_state",
                            "entity_id": "sensor.trigger_numeric_state",
                            "above": 10,
                        },
                        {
                            "trigger": "calendar",
                            "entity_id": "calendar.trigger_calendar",
                            "event": "start",
                        },
                        {
                            "trigger": "event",
                            "event_type": "state_changed",
                            "event_data": {"entity_id": "sensor.trigger_event"},
                        },
                        # entity_id is a list of strings (not supported)
                        {
                            "trigger": "event",
                            "event_type": "state_changed",
                            "event_data": {"entity_id": ["sensor.trigger_event2"]},
                        },
                        # entity_id is not a valid entity ID
                        {
                            "trigger": "event",
                            "event_type": "state_changed",
                            "event_data": {"entity_id": "abc"},
                        },
                        # entity_id is not a string
                        {
                            "trigger": "event",
                            "event_type": "state_changed",
                            "event_data": {"entity_id": 123},
                        },
                    ],
                    "conditions": {
                        "condition": "state",
                        "entity_id": "light.condition_state",
                        "state": "on",
                    },
                    "actions": [
                        {
                            "action": "test.script",
                            "data": {"entity_id": "light.in_both"},
                        },
                        {
                            "action": "test.script",
                            "data": {"entity_id": "light.in_first"},
                        },
                        {
                            "domain": "light",
                            "device_id": device_in_both.id,
                            "entity_id": "light.bla",
                            "type": "turn_on",
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
                    ],
                },
                {
                    "alias": "test2",
                    "triggers": [
                        {
                            "trigger": "device",
                            "domain": "light",
                            "type": "turned_on",
                            "entity_id": "light.trigger_2",
                            "device_id": trigger_device_2.id,
                        },
                        {
                            "trigger": "tag",
                            "tag_id": "1234",
                            "device_id": "device-trigger-tag1",
                        },
                        {
                            "trigger": "tag",
                            "tag_id": "1234",
                            "device_id": ["device-trigger-tag2", "device-trigger-tag3"],
                        },
                        {
                            "trigger": "event",
                            "event_type": "esphome.button_pressed",
                            "event_data": {"device_id": "device-trigger-event"},
                        },
                        # device_id is a list of strings (not supported)
                        {
                            "trigger": "event",
                            "event_type": "esphome.button_pressed",
                            "event_data": {"device_id": ["device-trigger-event2"]},
                        },
                        # device_id is not a string
                        {
                            "trigger": "event",
                            "event_type": "esphome.button_pressed",
                            "event_data": {"device_id": 123},
                        },
                    ],
                    "conditions": {
                        "condition": "device",
                        "device_id": condition_device.id,
                        "domain": "light",
                        "type": "is_on",
                        "entity_id": "light.bla",
                    },
                    "actions": [
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
                            "domain": "light",
                            "device_id": device_in_both.id,
                            "entity_id": "light.bla",
                            "type": "turn_on",
                        },
                        {
                            "domain": "light",
                            "device_id": device_in_last.id,
                            "entity_id": "light.bla",
                            "type": "turn_on",
                        },
                    ],
                },
                {
                    "alias": "test3",
                    "triggers": [
                        {
                            "trigger": "event",
                            "event_type": "esphome.button_pressed",
                            "event_data": {"area_id": "area-trigger-event"},
                        },
                        # area_id is a list of strings (not supported)
                        {
                            "trigger": "event",
                            "event_type": "esphome.button_pressed",
                            "event_data": {"area_id": ["area-trigger-event2"]},
                        },
                        # area_id is not a string
                        {
                            "trigger": "event",
                            "event_type": "esphome.button_pressed",
                            "event_data": {"area_id": 123},
                        },
                    ],
                    "conditions": {
                        "condition": "device",
                        "device_id": condition_device.id,
                        "domain": "light",
                        "type": "is_on",
                        "entity_id": "light.bla",
                    },
                    "actions": [
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
            ]
        },
    )

    assert set(automation.automations_with_entity(hass, "light.in_both")) == {
        "automation.test1",
        "automation.test2",
        "automation.test3",
    }
    assert set(automation.entities_in_automation(hass, "automation.test1")) == {
        "calendar.trigger_calendar",
        "sensor.trigger_state",
        "sensor.trigger_numeric_state",
        "sensor.trigger_event",
        "light.condition_state",
        "light.in_both",
        "light.in_first",
    }
    assert set(automation.automations_with_device(hass, device_in_both.id)) == {
        "automation.test1",
        "automation.test2",
    }
    assert set(automation.devices_in_automation(hass, "automation.test2")) == {
        trigger_device_2.id,
        condition_device.id,
        device_in_both.id,
        device_in_last.id,
        "device-trigger-event",
        "device-trigger-tag1",
        "device-trigger-tag2",
        "device-trigger-tag3",
    }
    assert set(automation.automations_with_area(hass, "area-in-both")) == {
        "automation.test1",
        "automation.test3",
    }
    assert set(automation.areas_in_automation(hass, "automation.test3")) == {
        "area-in-both",
        "area-in-last",
    }
    assert set(automation.automations_with_floor(hass, "floor-in-both")) == {
        "automation.test1",
        "automation.test3",
    }
    assert set(automation.floors_in_automation(hass, "automation.test3")) == {
        "floor-in-both",
        "floor-in-last",
    }
    assert set(automation.automations_with_label(hass, "label-in-both")) == {
        "automation.test1",
        "automation.test3",
    }
    assert set(automation.labels_in_automation(hass, "automation.test3")) == {
        "label-in-both",
        "label-in-last",
    }
    assert automation.blueprint_in_automation(hass, "automation.test3") is None