async def test_errornous_value_template(
    hass: HomeAssistant,
    mqtt_mock_entry: MqttMockHAClientGenerator,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test that it fetches the given payload with a template or handles the exception."""
    state_topic = "test/update"
    await mqtt_mock_entry()

    # Simulate a template redendering error with payload
    # without "update" mapping
    example_payload: dict[str, Any] = {
        "child_lock": "UNLOCK",
        "current": 0.02,
        "energy": 212.92,
        "indicator_mode": "off/on",
        "linkquality": 65,
        "power": 0,
        "power_outage_memory": "off",
        "state": "ON",
        "voltage": 232,
    }

    async_fire_mqtt_message(hass, state_topic, json.dumps(example_payload))
    await hass.async_block_till_done()
    assert hass.states.get("update.test_update") is not None
    assert "Unable to process payload '" in caplog.text

    # Add update info
    example_payload["update"] = {
        "latest_version": "2.0.0",
        "installed_version": "1.9.0",
        "progress": 20,
    }

    async_fire_mqtt_message(hass, state_topic, json.dumps(example_payload))
    await hass.async_block_till_done()

    state = hass.states.get("update.test_update")
    assert state is not None

    assert state.state == STATE_ON
    assert state.attributes.get("installed_version") == "1.9.0"
    assert state.attributes.get("latest_version") == "2.0.0"
    assert state.attributes.get("update_percentage") == 20