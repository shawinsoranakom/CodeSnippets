async def test_get_alexa_entity(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    hass_ws_client: WebSocketGenerator,
    setup_cloud: None,
) -> None:
    """Test that we can get an Alexa entity."""
    client = await hass_ws_client(hass)

    # Test getting an unknown entity
    await client.send_json_auto_id(
        {"type": "cloud/alexa/entities/get", "entity_id": "light.kitchen"}
    )
    response = await client.receive_json()

    assert response["success"]
    assert response["result"] is None

    # Test getting an unknown sensor
    await client.send_json_auto_id(
        {"type": "cloud/alexa/entities/get", "entity_id": "sensor.temperature"}
    )
    response = await client.receive_json()

    assert not response["success"]
    assert response["error"] == {
        "code": "not_supported",
        "message": "sensor.temperature not supported by Alexa",
    }

    # Test getting a blocked entity
    entity_registry.async_get_or_create(
        "group", "test", "unique", suggested_object_id="all_locks"
    )
    hass.states.async_set("group.all_locks", "bla")

    await client.send_json_auto_id(
        {"type": "cloud/alexa/entities/get", "entity_id": "group.all_locks"}
    )
    response = await client.receive_json()

    assert not response["success"]
    assert response["error"] == {
        "code": "not_supported",
        "message": "group.all_locks not supported by Alexa",
    }

    entity_registry.async_get_or_create(
        "light", "test", "unique", suggested_object_id="kitchen"
    )
    entity_registry.async_get_or_create(
        "water_heater", "test", "unique", suggested_object_id="basement"
    )

    await client.send_json_auto_id(
        {"type": "cloud/alexa/entities/get", "entity_id": "light.kitchen"}
    )
    response = await client.receive_json()

    assert response["success"]
    assert response["result"] is None

    await client.send_json_auto_id(
        {"type": "cloud/alexa/entities/get", "entity_id": "water_heater.basement"}
    )
    response = await client.receive_json()

    assert not response["success"]
    assert response["error"] == {
        "code": "not_supported",
        "message": "water_heater.basement not supported by Alexa",
    }