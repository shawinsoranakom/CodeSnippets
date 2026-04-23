async def test_if_fires_on_for_condition(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
    service_calls: list[ServiceCall],
    mock_binary_sensor_entities: dict[str, MockBinarySensor],
) -> None:
    """Test for firing if condition is on with delay."""
    point1 = dt_util.utcnow()
    point2 = point1 + timedelta(seconds=10)
    point3 = point2 + timedelta(seconds=10)

    setup_test_component_platform(hass, DOMAIN, mock_binary_sensor_entities.values())
    assert await async_setup_component(hass, DOMAIN, {DOMAIN: {CONF_PLATFORM: "test"}})
    await hass.async_block_till_done()

    config_entry = MockConfigEntry(domain="test", data={})
    config_entry.add_to_hass(hass)
    device_entry = device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        connections={(dr.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
    )
    entry = entity_registry.async_get(mock_binary_sensor_entities["battery"].entity_id)
    entity_registry.async_update_entity(entry.entity_id, device_id=device_entry.id)

    with freeze_time(point1) as time_freeze:
        assert await async_setup_component(
            hass,
            automation.DOMAIN,
            {
                automation.DOMAIN: [
                    {
                        "trigger": {"platform": "event", "event_type": "test_event1"},
                        "condition": {
                            "condition": "device",
                            "domain": DOMAIN,
                            "device_id": device_entry.id,
                            "entity_id": entry.id,
                            "type": "is_not_bat_low",
                            "for": {"seconds": 5},
                        },
                        "action": {
                            "service": "test.automation",
                            "data_template": {
                                "some": (
                                    "is_off {{ trigger.platform }}"
                                    " - {{ trigger.event.event_type }}"
                                )
                            },
                        },
                    }
                ]
            },
        )
        await hass.async_block_till_done()
        assert hass.states.get(entry.entity_id).state == STATE_ON
        assert len(service_calls) == 0

        hass.bus.async_fire("test_event1")
        await hass.async_block_till_done()
        assert len(service_calls) == 0

        # Time travel 10 secs into the future
        time_freeze.move_to(point2)
        hass.bus.async_fire("test_event1")
        await hass.async_block_till_done()
        assert len(service_calls) == 0

        hass.states.async_set(entry.entity_id, STATE_OFF)
        hass.bus.async_fire("test_event1")
        await hass.async_block_till_done()
        assert len(service_calls) == 0

        # Time travel 20 secs into the future
        time_freeze.move_to(point3)
        hass.bus.async_fire("test_event1")
        await hass.async_block_till_done()
        assert len(service_calls) == 1
        assert service_calls[0].data["some"] == "is_off event - test_event1"