async def test_if_tilt_position(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
    service_calls: list[ServiceCall],
    caplog: pytest.LogCaptureFixture,
    mock_cover_entities: list[MockCover],
) -> None:
    """Test for tilt position conditions."""
    setup_test_component_platform(hass, DOMAIN, mock_cover_entities)
    ent = mock_cover_entities[3]
    assert await async_setup_component(hass, DOMAIN, {DOMAIN: {CONF_PLATFORM: "test"}})
    await hass.async_block_till_done()

    config_entry = MockConfigEntry(domain="test", data={})
    config_entry.add_to_hass(hass)
    device_entry = device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        connections={(dr.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
    )
    entry = entity_registry.async_get(ent.entity_id)
    entity_registry.async_update_entity(entry.entity_id, device_id=device_entry.id)

    assert await async_setup_component(
        hass,
        automation.DOMAIN,
        {
            automation.DOMAIN: [
                {
                    "trigger": {"platform": "event", "event_type": "test_event1"},
                    "action": {
                        "choose": {
                            "conditions": {
                                "condition": "device",
                                "domain": DOMAIN,
                                "device_id": device_entry.id,
                                "entity_id": entry.id,
                                "type": "is_tilt_position",
                                "above": 45,
                            },
                            "sequence": {
                                "service": "test.automation",
                                "data_template": {
                                    "some": (
                                        "is_pos_gt_45 "
                                        "- {{ trigger.platform }} "
                                        "- {{ trigger.event.event_type }}"
                                    )
                                },
                            },
                        },
                        "default": {
                            "service": "test.automation",
                            "data_template": {
                                "some": (
                                    "is_pos_not_gt_45 "
                                    "- {{ trigger.platform }} "
                                    "- {{ trigger.event.event_type }}"
                                )
                            },
                        },
                    },
                },
                {
                    "trigger": {"platform": "event", "event_type": "test_event2"},
                    "condition": [
                        {
                            "condition": "device",
                            "domain": DOMAIN,
                            "device_id": device_entry.id,
                            "entity_id": entry.id,
                            "type": "is_tilt_position",
                            "below": 90,
                        }
                    ],
                    "action": {
                        "service": "test.automation",
                        "data_template": {
                            "some": (
                                "is_pos_lt_90 "
                                "- {{ trigger.platform }} "
                                "- {{ trigger.event.event_type }}"
                            )
                        },
                    },
                },
                {
                    "trigger": {"platform": "event", "event_type": "test_event3"},
                    "condition": [
                        {
                            "condition": "device",
                            "domain": DOMAIN,
                            "device_id": device_entry.id,
                            "entity_id": entry.id,
                            "type": "is_tilt_position",
                            "above": 45,
                            "below": 90,
                        }
                    ],
                    "action": {
                        "service": "test.automation",
                        "data_template": {
                            "some": (
                                "is_pos_gt_45_lt_90 "
                                "- {{ trigger.platform }} "
                                "- {{ trigger.event.event_type }}"
                            )
                        },
                    },
                },
            ]
        },
    )

    caplog.clear()

    hass.bus.async_fire("test_event1")
    await hass.async_block_till_done()
    hass.bus.async_fire("test_event2")
    await hass.async_block_till_done()
    hass.bus.async_fire("test_event3")
    await hass.async_block_till_done()
    assert len(service_calls) == 3
    assert service_calls[0].data["some"] == "is_pos_gt_45 - event - test_event1"
    assert service_calls[1].data["some"] == "is_pos_lt_90 - event - test_event2"
    assert service_calls[2].data["some"] == "is_pos_gt_45_lt_90 - event - test_event3"

    hass.states.async_set(
        ent.entity_id, CoverState.CLOSED, attributes={"current_tilt_position": 45}
    )
    hass.bus.async_fire("test_event1")
    await hass.async_block_till_done()
    hass.bus.async_fire("test_event2")
    await hass.async_block_till_done()
    hass.bus.async_fire("test_event3")
    await hass.async_block_till_done()
    assert len(service_calls) == 5
    assert service_calls[3].data["some"] == "is_pos_not_gt_45 - event - test_event1"
    assert service_calls[4].data["some"] == "is_pos_lt_90 - event - test_event2"

    hass.states.async_set(
        ent.entity_id, CoverState.CLOSED, attributes={"current_tilt_position": 90}
    )
    hass.bus.async_fire("test_event1")
    await hass.async_block_till_done()
    hass.bus.async_fire("test_event2")
    await hass.async_block_till_done()
    hass.bus.async_fire("test_event3")
    await hass.async_block_till_done()
    assert len(service_calls) == 6
    assert service_calls[5].data["some"] == "is_pos_gt_45 - event - test_event1"

    hass.states.async_set(ent.entity_id, STATE_UNAVAILABLE, attributes={})
    hass.bus.async_fire("test_event1")
    await hass.async_block_till_done()
    assert len(service_calls) == 7
    assert service_calls[6].data["some"] == "is_pos_not_gt_45 - event - test_event1"

    for record in caplog.records:
        assert record.levelname in ("DEBUG", "INFO")