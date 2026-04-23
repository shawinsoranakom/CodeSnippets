async def test_change_state_via_mqtt(
    hass: HomeAssistant, mqtt_mock: MqttMockHAClient, setup_pglab
) -> None:
    """Test state update via MQTT."""

    payload = get_device_discovery_payload(
        number_of_shutters=0,
        number_of_boards=1,
    )

    await send_discovery_message(hass, payload)

    # Simulate response from the device
    state = hass.states.get("switch.test_relay_0")
    assert state.state == STATE_UNKNOWN
    assert not state.attributes.get(ATTR_ASSUMED_STATE)

    # Turn relay OFF
    async_fire_mqtt_message(hass, "pglab/test/relay/0/state", "OFF")
    await hass.async_block_till_done()
    state = hass.states.get("switch.test_relay_0")
    assert not state.attributes.get(ATTR_ASSUMED_STATE)
    assert state.state == STATE_OFF

    # Turn relay ON
    async_fire_mqtt_message(hass, "pglab/test/relay/0/state", "ON")
    await hass.async_block_till_done()
    state = hass.states.get("switch.test_relay_0")
    assert state.state == STATE_ON

    # Turn relay OFF
    async_fire_mqtt_message(hass, "pglab/test/relay/0/state", "OFF")
    await hass.async_block_till_done()
    state = hass.states.get("switch.test_relay_0")
    assert state.state == STATE_OFF

    # Turn relay ON
    async_fire_mqtt_message(hass, "pglab/test/relay/0/state", "ON")
    await hass.async_block_till_done()
    state = hass.states.get("switch.test_relay_0")
    assert state.state == STATE_ON