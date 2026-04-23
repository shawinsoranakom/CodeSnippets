async def test_expose_entity_unknown(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
) -> None:
    """Test behavior when exposing an unknown entity."""
    ws_client = await hass_ws_client(hass)
    assert await async_setup_component(hass, "homeassistant", {})
    await hass.async_block_till_done()

    exposed_entities = hass.data[DATA_EXPOSED_ENTITIES]
    assert len(exposed_entities.entities) == 0

    # Set options
    await ws_client.send_json_auto_id(
        {
            "type": "homeassistant/expose_entity",
            "assistants": ["cloud.alexa"],
            "entity_ids": ["test.test"],
            "should_expose": True,
        }
    )

    response = await ws_client.receive_json()
    assert response["success"]

    assert len(exposed_entities.entities) == 1
    assert exposed_entities.entities == {
        "test.test": ExposedEntity({"cloud.alexa": {"should_expose": True}})
    }

    # Update options
    await ws_client.send_json_auto_id(
        {
            "type": "homeassistant/expose_entity",
            "assistants": ["cloud.alexa", "cloud.google_assistant"],
            "entity_ids": ["test.test", "test.test2"],
            "should_expose": False,
        }
    )

    response = await ws_client.receive_json()
    assert response["success"]

    assert len(exposed_entities.entities) == 2
    assert exposed_entities.entities == {
        "test.test": ExposedEntity(
            {
                "cloud.alexa": {"should_expose": False},
                "cloud.google_assistant": {"should_expose": False},
            }
        ),
        "test.test2": ExposedEntity(
            {
                "cloud.alexa": {"should_expose": False},
                "cloud.google_assistant": {"should_expose": False},
            }
        ),
    }