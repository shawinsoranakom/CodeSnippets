async def test_discovery_update(
    hass: HomeAssistant, mqtt_mock: MqttMockHAClient, setup_pglab
) -> None:
    """Update discovery message and  check if relay are property updated."""

    payload = get_device_discovery_payload(
        device_name="first_test",
        number_of_shutters=0,
        number_of_boards=1,
    )

    await send_discovery_message(hass, payload)

    # test the available relay in the first configuration
    for i in range(8):
        state = hass.states.get(f"switch.first_test_relay_{i}")
        assert state.state == STATE_UNKNOWN
        assert not state.attributes.get(ATTR_ASSUMED_STATE)

    # prepare a new message ... the same device but renamed
    # and with different relay configuration
    payload = get_device_discovery_payload(
        device_name="second_test",
        number_of_shutters=0,
        number_of_boards=2,
    )

    await send_discovery_message(hass, payload)

    # entity id from the old relay configuration should be reused
    for i in range(8):
        state = hass.states.get(f"switch.first_test_relay_{i}")
        assert state.state == STATE_UNKNOWN
        assert not state.attributes.get(ATTR_ASSUMED_STATE)
    for i in range(8):
        assert not hass.states.get(f"switch.second_test_relay_{i}")

    # check new relay
    for i in range(8, 16):
        state = hass.states.get(f"switch.second_test_relay_{i}")
        assert state.state == STATE_UNKNOWN
        assert not state.attributes.get(ATTR_ASSUMED_STATE)