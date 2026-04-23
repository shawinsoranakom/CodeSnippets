async def test_switches_softener(
    hass: HomeAssistant, mqtt_mock: MqttMockHAClient
) -> None:
    """Test DROP switches for softeners."""
    entry = config_entry_softener()
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)

    bypass_switch_name = "switch.softener_treatment_bypass"
    assert hass.states.get(bypass_switch_name).state == STATE_UNKNOWN

    async_fire_mqtt_message(hass, TEST_DATA_SOFTENER_TOPIC, TEST_DATA_SOFTENER_RESET)
    await hass.async_block_till_done()
    assert hass.states.get(bypass_switch_name).state == STATE_ON

    async_fire_mqtt_message(hass, TEST_DATA_SOFTENER_TOPIC, TEST_DATA_SOFTENER)
    await hass.async_block_till_done()
    assert hass.states.get(bypass_switch_name).state == STATE_OFF

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
    async_fire_mqtt_message(hass, TEST_DATA_SOFTENER_TOPIC, TEST_DATA_SOFTENER_RESET)
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
    async_fire_mqtt_message(hass, TEST_DATA_SOFTENER_TOPIC, TEST_DATA_SOFTENER)
    await hass.async_block_till_done()
    assert hass.states.get(bypass_switch_name).state == STATE_OFF