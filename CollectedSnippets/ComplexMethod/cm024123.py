async def test_mqtt_ws_subscription(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    mqtt_mock_entry: MqttMockHAClientGenerator,
) -> None:
    """Test MQTT websocket subscription."""
    await mqtt_mock_entry()
    client = await hass_ws_client(hass)
    await client.send_json({"id": 5, "type": "mqtt/subscribe", "topic": "test-topic"})
    response = await client.receive_json()
    assert response["success"]

    async_fire_mqtt_message(hass, "test-topic", "test1")
    async_fire_mqtt_message(hass, "test-topic", "test2")
    async_fire_mqtt_message(hass, "test-topic", b"\xde\xad\xbe\xef")

    response = await client.receive_json()
    assert response["event"]["topic"] == "test-topic"
    assert response["event"]["payload"] == "test1"

    response = await client.receive_json()
    assert response["event"]["topic"] == "test-topic"
    assert response["event"]["payload"] == "test2"

    response = await client.receive_json()
    assert response["event"]["topic"] == "test-topic"
    assert response["event"]["payload"] == "b'\\xde\\xad\\xbe\\xef'"

    # Unsubscribe
    await client.send_json({"id": 8, "type": "unsubscribe_events", "subscription": 5})
    response = await client.receive_json()
    assert response["success"]

    # Subscribe with QoS 2
    await client.send_json(
        {"id": 9, "type": "mqtt/subscribe", "topic": "test-topic", "qos": 2}
    )
    response = await client.receive_json()
    assert response["success"]

    async_fire_mqtt_message(hass, "test-topic", "test1", 2)
    async_fire_mqtt_message(hass, "test-topic", "test2", 2)
    async_fire_mqtt_message(hass, "test-topic", b"\xde\xad\xbe\xef", 2)

    response = await client.receive_json()
    assert response["event"]["topic"] == "test-topic"
    assert response["event"]["payload"] == "test1"
    assert response["event"]["qos"] == 2

    response = await client.receive_json()
    assert response["event"]["topic"] == "test-topic"
    assert response["event"]["payload"] == "test2"
    assert response["event"]["qos"] == 2

    response = await client.receive_json()
    assert response["event"]["topic"] == "test-topic"
    assert response["event"]["payload"] == "b'\\xde\\xad\\xbe\\xef'"
    assert response["event"]["qos"] == 2

    # Unsubscribe
    await client.send_json({"id": 15, "type": "unsubscribe_events", "subscription": 9})
    response = await client.receive_json()
    assert response["success"]