async def test_switches_hub(hass: HomeAssistant, mqtt_mock: MqttMockHAClient) -> None:
    """Test DROP switches for hubs."""
    entry = config_entry_hub()
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)

    water_supply_switch_name = "switch.hub_drop_1_c0ffee_water_supply"
    assert hass.states.get(water_supply_switch_name).state == STATE_UNKNOWN
    bypass_switch_name = "switch.hub_drop_1_c0ffee_treatment_bypass"
    assert hass.states.get(bypass_switch_name).state == STATE_UNKNOWN

    async_fire_mqtt_message(hass, TEST_DATA_HUB_TOPIC, TEST_DATA_HUB_RESET)
    await hass.async_block_till_done()
    assert hass.states.get(water_supply_switch_name).state == STATE_OFF
    assert hass.states.get(bypass_switch_name).state == STATE_ON

    async_fire_mqtt_message(hass, TEST_DATA_HUB_TOPIC, TEST_DATA_HUB)
    await hass.async_block_till_done()
    assert hass.states.get(water_supply_switch_name).state == STATE_ON
    assert hass.states.get(bypass_switch_name).state == STATE_OFF

    # Test switch turn off method.
    mqtt_mock.async_publish.reset_mock()
    await hass.services.async_call(
        SWITCH_DOMAIN,
        SERVICE_TURN_OFF,
        {ATTR_ENTITY_ID: water_supply_switch_name},
        blocking=True,
    )
    assert len(mqtt_mock.async_publish.mock_calls) == 1

    # Simulate response from the hub
    async_fire_mqtt_message(hass, TEST_DATA_HUB_TOPIC, TEST_DATA_HUB_RESET)
    await hass.async_block_till_done()
    assert hass.states.get(water_supply_switch_name).state == STATE_OFF

    # Test switch turn on method.
    mqtt_mock.async_publish.reset_mock()
    await hass.services.async_call(
        SWITCH_DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: water_supply_switch_name},
        blocking=True,
    )
    assert len(mqtt_mock.async_publish.mock_calls) == 1

    # Simulate response from the hub
    async_fire_mqtt_message(hass, TEST_DATA_HUB_TOPIC, TEST_DATA_HUB)
    await hass.async_block_till_done()
    assert hass.states.get(water_supply_switch_name).state == STATE_ON

    # Test switch turn on method.
    mqtt_mock.async_publish.reset_mock()
    await hass.services.async_call(
        SWITCH_DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: bypass_switch_name},
        blocking=True,
    )
    assert len(mqtt_mock.async_publish.mock_calls) == 1

    # Simulate response from the device
    async_fire_mqtt_message(hass, TEST_DATA_HUB_TOPIC, TEST_DATA_HUB_RESET)
    await hass.async_block_till_done()
    assert hass.states.get(bypass_switch_name).state == STATE_ON

    # Test switch turn off method.
    mqtt_mock.async_publish.reset_mock()
    await hass.services.async_call(
        SWITCH_DOMAIN,
        SERVICE_TURN_OFF,
        {ATTR_ENTITY_ID: bypass_switch_name},
        blocking=True,
    )
    assert len(mqtt_mock.async_publish.mock_calls) == 1

    # Simulate response from the device
    async_fire_mqtt_message(hass, TEST_DATA_HUB_TOPIC, TEST_DATA_HUB)
    await hass.async_block_till_done()
    assert hass.states.get(bypass_switch_name).state == STATE_OFF