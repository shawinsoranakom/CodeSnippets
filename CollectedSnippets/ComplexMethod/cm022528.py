async def test_expose_entity(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    hass_ws_client: WebSocketGenerator,
) -> None:
    """Test expose entity."""
    ws_client = await hass_ws_client(hass)
    assert await async_setup_component(hass, "homeassistant", {})
    await hass.async_block_till_done()

    entry1 = entity_registry.async_get_or_create("test", "test", "unique1")
    entry2 = entity_registry.async_get_or_create("test", "test", "unique2")

    exposed_entities = hass.data[DATA_EXPOSED_ENTITIES]
    assert len(exposed_entities.entities) == 0

    # Set options
    await ws_client.send_json_auto_id(
        {
            "type": "homeassistant/expose_entity",
            "assistants": ["cloud.alexa"],
            "entity_ids": [entry1.entity_id],
            "should_expose": True,
        }
    )

    response = await ws_client.receive_json()
    assert response["success"]

    entry1 = entity_registry.async_get(entry1.entity_id)
    assert entry1.options == {"cloud.alexa": {"should_expose": True}}
    entry2 = entity_registry.async_get(entry2.entity_id)
    assert entry2.options == {}
    assert len(exposed_entities.entities) == 0

    # Update options
    await ws_client.send_json_auto_id(
        {
            "type": "homeassistant/expose_entity",
            "assistants": ["cloud.alexa", "cloud.google_assistant"],
            "entity_ids": [entry1.entity_id, entry2.entity_id],
            "should_expose": False,
        }
    )

    response = await ws_client.receive_json()
    assert response["success"]

    entry1 = entity_registry.async_get(entry1.entity_id)
    assert entry1.options == {
        "cloud.alexa": {"should_expose": False},
        "cloud.google_assistant": {"should_expose": False},
    }
    entry2 = entity_registry.async_get(entry2.entity_id)
    assert entry2.options == {
        "cloud.alexa": {"should_expose": False},
        "cloud.google_assistant": {"should_expose": False},
    }
    assert len(exposed_entities.entities) == 0