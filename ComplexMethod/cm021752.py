async def test_if_fires_on_position(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
    mock_cover_entities: list[MockCover],
    service_calls: list[ServiceCall],
) -> None:
    """Test for position triggers."""
    setup_test_component_platform(hass, DOMAIN, mock_cover_entities)
    ent = mock_cover_entities[1]
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
                    "trigger": [
                        {
                            "platform": "device",
                            "domain": DOMAIN,
                            "device_id": device_entry.id,
                            "entity_id": entry.id,
                            "type": "position",
                            "above": 45,
                        }
                    ],
                    "action": {
                        "service": "test.automation",
                        "data_template": {
                            "some": (
                                "is_pos_gt_45 "
                                "- {{ trigger.platform }} "
                                "- {{ trigger.entity_id }} "
                                "- {{ trigger.from_state.state }} "
                                "- {{ trigger.to_state.state }} "
                                "- {{ trigger.for }}"
                            )
                        },
                    },
                },
                {
                    "trigger": [
                        {
                            "platform": "device",
                            "domain": DOMAIN,
                            "device_id": device_entry.id,
                            "entity_id": entry.id,
                            "type": "position",
                            "below": 90,
                        }
                    ],
                    "action": {
                        "service": "test.automation",
                        "data_template": {
                            "some": (
                                "is_pos_lt_90 "
                                "- {{ trigger.platform }} "
                                "- {{ trigger.entity_id }} "
                                "- {{ trigger.from_state.state }} "
                                "- {{ trigger.to_state.state }} "
                                "- {{ trigger.for }}"
                            )
                        },
                    },
                },
                {
                    "trigger": [
                        {
                            "platform": "device",
                            "domain": DOMAIN,
                            "device_id": device_entry.id,
                            "entity_id": entry.id,
                            "type": "position",
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
                                "- {{ trigger.entity_id }} "
                                "- {{ trigger.from_state.state }} "
                                "- {{ trigger.to_state.state }} "
                                "- {{ trigger.for }}"
                            )
                        },
                    },
                },
            ]
        },
    )
    hass.states.async_set(
        ent.entity_id, CoverState.OPEN, attributes={"current_position": 1}
    )
    hass.states.async_set(
        ent.entity_id, CoverState.CLOSED, attributes={"current_position": 95}
    )
    hass.states.async_set(
        ent.entity_id, CoverState.OPEN, attributes={"current_position": 50}
    )
    await hass.async_block_till_done()
    assert len(service_calls) == 3
    assert sorted(
        [
            service_calls[0].data["some"],
            service_calls[1].data["some"],
            service_calls[2].data["some"],
        ]
    ) == sorted(
        [
            f"is_pos_gt_45_lt_90 - device - {entry.entity_id} - closed - open - None",
            f"is_pos_lt_90 - device - {entry.entity_id} - closed - open - None",
            f"is_pos_gt_45 - device - {entry.entity_id} - open - closed - None",
        ]
    )

    hass.states.async_set(
        ent.entity_id, CoverState.CLOSED, attributes={"current_position": 95}
    )
    await hass.async_block_till_done()
    hass.states.async_set(
        ent.entity_id, CoverState.CLOSED, attributes={"current_position": 45}
    )
    await hass.async_block_till_done()
    assert len(service_calls) == 4
    assert (
        service_calls[3].data["some"]
        == f"is_pos_lt_90 - device - {entry.entity_id} - closed - closed - None"
    )

    hass.states.async_set(
        ent.entity_id, CoverState.CLOSED, attributes={"current_position": 90}
    )
    await hass.async_block_till_done()
    assert len(service_calls) == 5
    assert (
        service_calls[4].data["some"]
        == f"is_pos_gt_45 - device - {entry.entity_id} - closed - closed - None"
    )