async def test_serialize_discovery_partly_fails(
    hass: HomeAssistant, caplog: pytest.LogCaptureFixture
) -> None:
    """Test we can partly serialize a discovery."""

    async def _mock_discovery() -> dict[str, Any]:
        request = get_new_request("Alexa.Discovery", "Discover")
        hass.states.async_set("switch.bla", "on", {"friendly_name": "My Switch"})
        hass.states.async_set("fan.bla", "on", {"friendly_name": "My Fan"})
        hass.states.async_set(
            "humidifier.bla", "on", {"friendly_name": "My Humidifier"}
        )
        hass.states.async_set(
            "sensor.bla",
            "20.1",
            {
                "friendly_name": "Livingroom temperature",
                "unit_of_measurement": UnitOfTemperature.CELSIUS,
                "device_class": "temperature",
            },
        )
        return await smart_home.async_handle_message(
            hass, get_default_config(hass), request
        )

    msg = await _mock_discovery()
    assert "event" in msg
    msg = msg["event"]
    assert len(msg["payload"]["endpoints"]) == 4
    endpoint_ids = {
        attributes["endpointId"] for attributes in msg["payload"]["endpoints"]
    }
    assert all(
        entity in endpoint_ids
        for entity in ("switch#bla", "fan#bla", "humidifier#bla", "sensor#bla")
    )

    # Simulate fetching the interfaces fails for fan entity
    with patch(
        "homeassistant.components.alexa.entities.FanCapabilities.interfaces",
        side_effect=TypeError(),
    ):
        msg = await _mock_discovery()
        assert "event" in msg
        msg = msg["event"]
        assert len(msg["payload"]["endpoints"]) == 3
        endpoint_ids = {
            attributes["endpointId"] for attributes in msg["payload"]["endpoints"]
        }
        assert all(
            entity in endpoint_ids
            for entity in ("switch#bla", "humidifier#bla", "sensor#bla")
        )
        assert "Unable to serialize fan.bla for discovery" in caplog.text
        caplog.clear()

    # Simulate serializing properties fails for sensor entity
    with patch(
        "homeassistant.components.alexa.entities.SensorCapabilities.default_display_categories",
        side_effect=ValueError(),
    ):
        msg = await _mock_discovery()
        assert "event" in msg
        msg = msg["event"]
        assert len(msg["payload"]["endpoints"]) == 3
        endpoint_ids = {
            attributes["endpointId"] for attributes in msg["payload"]["endpoints"]
        }
        assert all(
            entity in endpoint_ids
            for entity in ("switch#bla", "humidifier#bla", "fan#bla")
        )
        assert "Unable to serialize sensor.bla for discovery" in caplog.text
        caplog.clear()