async def test_image_from_url(
    hass: HomeAssistant,
    hass_client_no_auth: ClientSessionGenerator,
    mqtt_mock_entry: MqttMockHAClientGenerator,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test setup with URL."""
    respx.get("http://localhost/test.png").respond(
        status_code=HTTPStatus.OK, content_type="image/png", content=b"milk"
    )
    topic = "test/image"

    await mqtt_mock_entry()

    # Test first with invalid URL
    async_fire_mqtt_message(hass, topic, b"/tmp/test.png")
    await hass.async_block_till_done()

    state = hass.states.get("image.test")
    assert state.state == "2023-04-01T00:00:00+00:00"

    assert "Invalid image URL" in caplog.text

    access_token = state.attributes["access_token"]
    assert state.attributes == {
        "access_token": access_token,
        "entity_picture": f"/api/image_proxy/image.test?token={access_token}",
        "friendly_name": "Test",
    }

    async_fire_mqtt_message(hass, topic, b"http://localhost/test.png")

    await hass.async_block_till_done()

    client = await hass_client_no_auth()
    resp = await client.get(state.attributes["entity_picture"])
    assert resp.status == HTTPStatus.OK
    body = await resp.text()
    assert body == "milk"
    assert respx.get("http://localhost/test.png").call_count == 1

    state = hass.states.get("image.test")
    assert state.state == "2023-04-01T00:00:00+00:00"

    # Check the image is not refetched
    resp = await client.get(state.attributes["entity_picture"])
    assert resp.status == HTTPStatus.OK
    body = await resp.text()
    assert body == "milk"
    assert respx.get("http://localhost/test.png").call_count == 1

    # Check the image is refetched when receiving a new message on the URL topic
    respx.get("http://localhost/test.png").respond(
        status_code=HTTPStatus.OK, content_type="image/png", content=b"milk"
    )
    async_fire_mqtt_message(hass, topic, b"http://localhost/test.png")

    await hass.async_block_till_done()

    resp = await client.get(state.attributes["entity_picture"])
    assert resp.status == HTTPStatus.OK
    body = await resp.text()
    assert body == "milk"
    assert respx.get("http://localhost/test.png").call_count == 2