async def test_cover_change_state_via_mqtt(
    hass: HomeAssistant, mqtt_mock: MqttMockHAClient, setup_pglab
) -> None:
    """Test state update via MQTT."""
    payload = get_device_discovery_payload(
        number_of_shutters=2,
        number_of_boards=1,
    )

    await send_discovery_message(hass, payload)

    # Check initial state is unknown
    cover = hass.states.get("cover.test_shutter_0")
    assert cover.state == STATE_UNKNOWN
    assert not cover.attributes.get(ATTR_ASSUMED_STATE)

    # Simulate the device responds sending mqtt messages and check if the cover state
    # change appropriately.

    async_fire_mqtt_message(hass, "pglab/test/shutter/0/state", "OPEN")
    await hass.async_block_till_done()
    cover = hass.states.get("cover.test_shutter_0")
    assert not cover.attributes.get(ATTR_ASSUMED_STATE)
    assert cover.state == STATE_OPEN

    async_fire_mqtt_message(hass, "pglab/test/shutter/0/state", "OPENING")
    await hass.async_block_till_done()
    cover = hass.states.get("cover.test_shutter_0")
    assert cover.state == STATE_OPENING

    async_fire_mqtt_message(hass, "pglab/test/shutter/0/state", "CLOSING")
    await hass.async_block_till_done()
    cover = hass.states.get("cover.test_shutter_0")
    assert cover.state == STATE_CLOSING

    async_fire_mqtt_message(hass, "pglab/test/shutter/0/state", "CLOSED")
    await hass.async_block_till_done()
    cover = hass.states.get("cover.test_shutter_0")
    assert cover.state == STATE_CLOSED