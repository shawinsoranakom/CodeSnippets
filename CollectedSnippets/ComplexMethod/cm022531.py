async def test_should_expose(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    hass_ws_client: WebSocketGenerator,
    entities: dict[str, str],
) -> None:
    """Test expose entity."""
    ws_client = await hass_ws_client(hass)
    assert await async_setup_component(hass, "homeassistant", {})
    await hass.async_block_till_done()

    # Expose new entities to Alexa
    await ws_client.send_json_auto_id(
        {
            "type": "homeassistant/expose_new_entities/set",
            "assistant": "cloud.alexa",
            "expose_new": True,
        }
    )
    response = await ws_client.receive_json()
    assert response["success"]

    # Unknown entity is not exposed
    assert async_should_expose(hass, "test.test", "test.test") is False

    # Blocked entity is not exposed
    assert async_should_expose(hass, "cloud.alexa", entities["blocked"]) is False

    # Lock is not exposed
    assert async_should_expose(hass, "cloud.alexa", entities["lock"]) is False

    # Binary sensor without device class is not exposed
    assert async_should_expose(hass, "cloud.alexa", entities["binary_sensor"]) is False

    # Binary sensor with certain device class is exposed
    assert async_should_expose(hass, "cloud.alexa", entities["door_sensor"]) is True

    # Sensor without device class is not exposed
    assert async_should_expose(hass, "cloud.alexa", entities["sensor"]) is False

    # Sensor with certain device class is exposed
    assert (
        async_should_expose(hass, "cloud.alexa", entities["temperature_sensor"]) is True
    )

    # Media player is exposed
    assert async_should_expose(hass, "cloud.alexa", entities["media_player"]) is True

    # The second time we check, it should load it from storage
    assert (
        async_should_expose(hass, "cloud.alexa", entities["temperature_sensor"]) is True
    )

    # Check with a different assistant
    exposed_entities = hass.data[DATA_EXPOSED_ENTITIES]
    exposed_entities.async_set_expose_new_entities("cloud.no_default_expose", False)
    assert (
        async_should_expose(
            hass, "cloud.no_default_expose", entities["temperature_sensor"]
        )
        is False
    )