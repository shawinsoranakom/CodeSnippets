async def test_run_image_b64_encoded(
    hass: HomeAssistant,
    hass_client_no_auth: ClientSessionGenerator,
    mqtt_mock_entry: MqttMockHAClientGenerator,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test that it fetches the given encoded payload."""
    topic = "test/image"
    await mqtt_mock_entry()

    state = hass.states.get("image.test")
    assert state.state == STATE_UNKNOWN
    access_token = state.attributes["access_token"]
    assert state.attributes == {
        "access_token": access_token,
        "entity_picture": f"/api/image_proxy/image.test?token={access_token}",
        "friendly_name": "Test",
    }

    # Fire incorrect encoded message (utf-8 encoded string)
    async_fire_mqtt_message(hass, topic, "grass")
    client = await hass_client_no_auth()
    resp = await client.get(state.attributes["entity_picture"])
    assert resp.status == HTTPStatus.INTERNAL_SERVER_ERROR
    assert "Error processing image data received at topic test/image" in caplog.text

    # Fire correctly encoded message (b64 encoded payload)
    async_fire_mqtt_message(hass, topic, b64encode(b"grass"))
    client = await hass_client_no_auth()
    resp = await client.get(state.attributes["entity_picture"])
    assert resp.status == HTTPStatus.OK
    body = await resp.read()
    assert body == b"grass"

    state = hass.states.get("image.test")
    assert state.state == "2023-04-01T00:00:00+00:00"