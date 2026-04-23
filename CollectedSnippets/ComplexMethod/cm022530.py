async def test_expose_new_entities(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    hass_ws_client: WebSocketGenerator,
    expose_new,
) -> None:
    """Test expose entity."""
    ws_client = await hass_ws_client(hass)
    assert await async_setup_component(hass, "homeassistant", {})
    await hass.async_block_till_done()

    entry1 = entity_registry.async_get_or_create("climate", "test", "unique1")
    entry2 = entity_registry.async_get_or_create("climate", "test", "unique2")

    await ws_client.send_json_auto_id(
        {
            "type": "homeassistant/expose_new_entities/get",
            "assistant": "cloud.alexa",
        }
    )
    response = await ws_client.receive_json()
    assert response["success"]
    assert response["result"] == {"expose_new": False}

    # Check if exposed - should be False
    assert async_should_expose(hass, "cloud.alexa", entry1.entity_id) is False

    # Expose new entities to Alexa
    await ws_client.send_json_auto_id(
        {
            "type": "homeassistant/expose_new_entities/set",
            "assistant": "cloud.alexa",
            "expose_new": expose_new,
        }
    )
    response = await ws_client.receive_json()
    assert response["success"]
    await ws_client.send_json_auto_id(
        {
            "type": "homeassistant/expose_new_entities/get",
            "assistant": "cloud.alexa",
        }
    )
    response = await ws_client.receive_json()
    assert response["success"]
    assert response["result"] == {"expose_new": expose_new}

    # Check again if exposed - should still be False
    assert async_should_expose(hass, "cloud.alexa", entry1.entity_id) is False

    # Check if exposed - should be True
    assert async_should_expose(hass, "cloud.alexa", entry2.entity_id) == expose_new