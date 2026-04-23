async def test_handle_events_late_setup(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
    get_next_aid: Callable[[], int],
    service_calls: list[ServiceCall],
) -> None:
    """Test that events are handled when setup happens after startup."""
    helper = await setup_test_component(hass, get_next_aid(), create_remote)

    entry = entity_registry.async_get("sensor.testdevice_battery")

    device = device_registry.async_get(entry.device_id)

    await hass.config_entries.async_unload(helper.config_entry.entry_id)
    await hass.async_block_till_done()
    assert helper.config_entry.state is ConfigEntryState.NOT_LOADED

    assert await async_setup_component(
        hass,
        automation.DOMAIN,
        {
            automation.DOMAIN: [
                {
                    "alias": "single_press",
                    "trigger": {
                        "platform": "device",
                        "domain": DOMAIN,
                        "device_id": device.id,
                        "type": "button1",
                        "subtype": "single_press",
                    },
                    "action": {
                        "service": "test.automation",
                        "data_template": {
                            "some": (
                                "{{ trigger.platform}} - "
                                "{{ trigger.type }} - {{ trigger.subtype }} - "
                                "{{ trigger.id }}"
                            )
                        },
                    },
                },
                {
                    "alias": "long_press",
                    "trigger": {
                        "platform": "device",
                        "domain": DOMAIN,
                        "device_id": device.id,
                        "type": "button2",
                        "subtype": "long_press",
                    },
                    "action": {
                        "service": "test.automation",
                        "data_template": {
                            "some": (
                                "{{ trigger.platform}} - "
                                "{{ trigger.type }} - {{ trigger.subtype }} - "
                                "{{ trigger.id }}"
                            )
                        },
                    },
                },
            ]
        },
    )
    await hass.async_block_till_done()

    await hass.config_entries.async_setup(helper.config_entry.entry_id)
    await hass.async_block_till_done()
    assert helper.config_entry.state is ConfigEntryState.LOADED

    # Make sure first automation (only) fires for single press
    helper.pairing.testing.update_named_service(
        "Button 1", {CharacteristicsTypes.INPUT_EVENT: 0}
    )

    await hass.async_block_till_done()
    assert len(service_calls) == 1
    assert service_calls[0].data["some"] == "device - button1 - single_press - 0"

    # Make sure automation doesn't trigger for a polled None
    helper.pairing.testing.update_named_service(
        "Button 1", {CharacteristicsTypes.INPUT_EVENT: None}
    )

    await hass.async_block_till_done()
    assert len(service_calls) == 1

    # Make sure automation doesn't trigger for long press
    helper.pairing.testing.update_named_service(
        "Button 1", {CharacteristicsTypes.INPUT_EVENT: 1}
    )

    await hass.async_block_till_done()
    assert len(service_calls) == 1

    # Make sure automation doesn't trigger for double press
    helper.pairing.testing.update_named_service(
        "Button 1", {CharacteristicsTypes.INPUT_EVENT: 2}
    )

    await hass.async_block_till_done()
    assert len(service_calls) == 1

    # Make sure second automation fires for long press
    helper.pairing.testing.update_named_service(
        "Button 2", {CharacteristicsTypes.INPUT_EVENT: 2}
    )

    await hass.async_block_till_done()
    assert len(service_calls) == 2
    assert service_calls[1].data["some"] == "device - button2 - long_press - 0"

    # Turn the automations off
    await hass.services.async_call(
        "automation",
        "turn_off",
        {"entity_id": "automation.long_press"},
        blocking=True,
    )
    assert len(service_calls) == 3

    await hass.services.async_call(
        "automation",
        "turn_off",
        {"entity_id": "automation.single_press"},
        blocking=True,
    )
    assert len(service_calls) == 4

    # Make sure event no longer fires
    helper.pairing.testing.update_named_service(
        "Button 2", {CharacteristicsTypes.INPUT_EVENT: 2}
    )

    await hass.async_block_till_done()
    assert len(service_calls) == 4