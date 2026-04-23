async def test_list_google_entities(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    hass_ws_client: WebSocketGenerator,
    setup_cloud: None,
) -> None:
    """Test that we can list Google entities."""
    client = await hass_ws_client(hass)
    entity = GoogleEntity(
        hass, MockConfig(should_expose=lambda *_: False), State("light.kitchen", "on")
    )
    entity2 = GoogleEntity(
        hass,
        MockConfig(should_expose=lambda *_: True, should_2fa=lambda *_: False),
        State("cover.garage", "open", {"device_class": "garage"}),
    )
    with patch(
        "homeassistant.components.google_assistant.helpers.async_get_entities",
        return_value=[entity, entity2],
    ):
        await client.send_json_auto_id({"type": "cloud/google_assistant/entities"})
        response = await client.receive_json()

    assert response["success"]
    assert len(response["result"]) == 2
    assert response["result"][0] == {
        "entity_id": "light.kitchen",
        "might_2fa": False,
        "traits": ["action.devices.traits.OnOff"],
    }
    assert response["result"][1] == {
        "entity_id": "cover.garage",
        "might_2fa": True,
        "traits": ["action.devices.traits.OpenClose"],
    }

    # Add the entities to the entity registry
    entity_registry.async_get_or_create(
        "light", "test", "unique", suggested_object_id="kitchen"
    )
    entity_registry.async_get_or_create(
        "cover", "test", "unique", suggested_object_id="garage"
    )

    with patch(
        "homeassistant.components.google_assistant.helpers.async_get_entities",
        return_value=[entity, entity2],
    ):
        await client.send_json_auto_id({"type": "cloud/google_assistant/entities"})
        response = await client.receive_json()

    assert response["success"]
    assert len(response["result"]) == 2
    assert response["result"][0] == {
        "entity_id": "light.kitchen",
        "might_2fa": False,
        "traits": ["action.devices.traits.OnOff"],
    }
    assert response["result"][1] == {
        "entity_id": "cover.garage",
        "might_2fa": True,
        "traits": ["action.devices.traits.OpenClose"],
    }