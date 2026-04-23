async def test_image_b64_encoded_with_availability(
    hass: HomeAssistant,
    hass_client_no_auth: ClientSessionGenerator,
    mqtt_mock_entry: MqttMockHAClientGenerator,
) -> None:
    """Test availability works if b64 encoding is turned on."""
    topic = "test/image"
    topic_availability = "test/image_availability"
    await mqtt_mock_entry()

    state = hass.states.get("image.test")
    assert state is not None
    assert state.state == STATE_UNAVAILABLE

    # Make sure we are available
    async_fire_mqtt_message(hass, topic_availability, "online")

    state = hass.states.get("image.test")
    assert state is not None
    assert state.state == STATE_UNKNOWN

    url = hass.states.get("image.test").attributes["entity_picture"]

    async_fire_mqtt_message(hass, topic, b64encode(b"grass"))

    client = await hass_client_no_auth()
    resp = await client.get(url)
    assert resp.status == HTTPStatus.OK
    body = await resp.text()
    assert body == "grass"

    state = hass.states.get("image.test")
    assert state.state == "2023-04-01T00:00:00+00:00"