async def test_list_exposed_entities(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    hass_ws_client: WebSocketGenerator,
) -> None:
    """Test list exposed entities."""
    ws_client = await hass_ws_client(hass)
    assert await async_setup_component(hass, "homeassistant", {})
    await hass.async_block_till_done()

    entry1 = entity_registry.async_get_or_create("test", "test", "unique1")
    entry2 = entity_registry.async_get_or_create("test", "test", "unique2")
    entity_registry.async_get_or_create("test", "test", "unique3")

    # Set options for registered entities
    await ws_client.send_json_auto_id(
        {
            "type": "homeassistant/expose_entity",
            "assistants": ["cloud.alexa", "cloud.google_assistant"],
            "entity_ids": [entry1.entity_id],
            "should_expose": True,
        }
    )
    response = await ws_client.receive_json()
    assert response["success"]

    await ws_client.send_json_auto_id(
        {
            "type": "homeassistant/expose_entity",
            "assistants": ["cloud.alexa", "cloud.google_assistant"],
            "entity_ids": [entry2.entity_id],
            "should_expose": False,
        }
    )
    response = await ws_client.receive_json()
    assert response["success"]

    # Set options for entities not in the entity registry
    await ws_client.send_json_auto_id(
        {
            "type": "homeassistant/expose_entity",
            "assistants": ["cloud.alexa", "cloud.google_assistant"],
            "entity_ids": ["test.test"],
            "should_expose": True,
        }
    )
    response = await ws_client.receive_json()
    assert response["success"]

    await ws_client.send_json_auto_id(
        {
            "type": "homeassistant/expose_entity",
            "assistants": ["cloud.alexa", "cloud.google_assistant"],
            "entity_ids": ["test.test2"],
            "should_expose": False,
        }
    )
    response = await ws_client.receive_json()
    assert response["success"]

    # List exposed entities
    await ws_client.send_json_auto_id({"type": "homeassistant/expose_entity/list"})
    response = await ws_client.receive_json()
    assert response["success"]
    assert response["result"] == {
        "exposed_entities": {
            "test.test": {"cloud.alexa": True, "cloud.google_assistant": True},
            "test.test_unique1": {"cloud.alexa": True, "cloud.google_assistant": True},
        },
    }