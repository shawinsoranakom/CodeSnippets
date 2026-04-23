async def test_action(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
    mock_alarm_control_panel_entities: dict[str, MockAlarm],
) -> None:
    """Test for turn_on and turn_off actions."""
    setup_test_component_platform(
        hass, DOMAIN, mock_alarm_control_panel_entities.values()
    )

    config_entry = MockConfigEntry(domain="test", data={})
    config_entry.add_to_hass(hass)
    device_entry = device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        connections={(dr.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
    )
    entity_entry = entity_registry.async_get_or_create(
        DOMAIN,
        "test",
        mock_alarm_control_panel_entities["no_arm_code"].unique_id,
        device_id=device_entry.id,
    )

    assert await async_setup_component(
        hass,
        automation.DOMAIN,
        {
            automation.DOMAIN: [
                {
                    "trigger": {
                        "platform": "event",
                        "event_type": "test_event_arm_away",
                    },
                    "action": {
                        "domain": DOMAIN,
                        "device_id": device_entry.id,
                        "entity_id": entity_entry.id,
                        "type": "arm_away",
                    },
                },
                {
                    "trigger": {
                        "platform": "event",
                        "event_type": "test_event_arm_home",
                    },
                    "action": {
                        "domain": DOMAIN,
                        "device_id": device_entry.id,
                        "entity_id": entity_entry.id,
                        "type": "arm_home",
                    },
                },
                {
                    "trigger": {
                        "platform": "event",
                        "event_type": "test_event_arm_night",
                    },
                    "action": {
                        "domain": DOMAIN,
                        "device_id": device_entry.id,
                        "entity_id": entity_entry.id,
                        "type": "arm_night",
                    },
                },
                {
                    "trigger": {
                        "platform": "event",
                        "event_type": "test_event_arm_vacation",
                    },
                    "action": {
                        "domain": DOMAIN,
                        "device_id": device_entry.id,
                        "entity_id": entity_entry.id,
                        "type": "arm_vacation",
                    },
                },
                {
                    "trigger": {"platform": "event", "event_type": "test_event_disarm"},
                    "action": {
                        "domain": DOMAIN,
                        "device_id": device_entry.id,
                        "entity_id": entity_entry.id,
                        "type": "disarm",
                        "code": "1234",
                    },
                },
                {
                    "trigger": {
                        "platform": "event",
                        "event_type": "test_event_trigger",
                    },
                    "action": {
                        "domain": DOMAIN,
                        "device_id": device_entry.id,
                        "entity_id": entity_entry.id,
                        "type": "trigger",
                    },
                },
            ]
        },
    )
    assert await async_setup_component(hass, DOMAIN, {DOMAIN: {CONF_PLATFORM: "test"}})
    await hass.async_block_till_done()

    assert hass.states.get(entity_entry.entity_id).state == STATE_UNKNOWN

    hass.bus.async_fire("test_event_arm_away")
    await hass.async_block_till_done()
    assert (
        hass.states.get(entity_entry.entity_id).state
        == AlarmControlPanelState.ARMED_AWAY
    )

    hass.bus.async_fire("test_event_arm_home")
    await hass.async_block_till_done()
    assert (
        hass.states.get(entity_entry.entity_id).state
        == AlarmControlPanelState.ARMED_HOME
    )

    hass.bus.async_fire("test_event_arm_vacation")
    await hass.async_block_till_done()
    assert (
        hass.states.get(entity_entry.entity_id).state
        == AlarmControlPanelState.ARMED_VACATION
    )

    hass.bus.async_fire("test_event_arm_night")
    await hass.async_block_till_done()
    assert (
        hass.states.get(entity_entry.entity_id).state
        == AlarmControlPanelState.ARMED_NIGHT
    )

    hass.bus.async_fire("test_event_disarm")
    await hass.async_block_till_done()
    assert (
        hass.states.get(entity_entry.entity_id).state == AlarmControlPanelState.DISARMED
    )

    hass.bus.async_fire("test_event_trigger")
    await hass.async_block_till_done()
    assert (
        hass.states.get(entity_entry.entity_id).state
        == AlarmControlPanelState.TRIGGERED
    )