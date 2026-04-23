async def test_get_google_entity(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    hass_ws_client: WebSocketGenerator,
    setup_cloud: None,
) -> None:
    """Test that we can get a Google entity."""
    client = await hass_ws_client(hass)

    # Test getting an unknown entity
    await client.send_json_auto_id(
        {"type": "cloud/google_assistant/entities/get", "entity_id": "light.kitchen"}
    )
    response = await client.receive_json()

    assert not response["success"]
    assert response["error"] == {
        "code": "not_found",
        "message": "light.kitchen unknown",
    }

    # Test getting a blocked entity
    entity_registry.async_get_or_create(
        "group", "test", "unique", suggested_object_id="all_locks"
    )
    hass.states.async_set("group.all_locks", "bla")

    await client.send_json_auto_id(
        {"type": "cloud/google_assistant/entities/get", "entity_id": "group.all_locks"}
    )
    response = await client.receive_json()

    assert not response["success"]
    assert response["error"] == {
        "code": "not_supported",
        "message": "group.all_locks not supported by Google assistant",
    }

    entity_registry.async_get_or_create(
        "light", "test", "unique", suggested_object_id="kitchen"
    )
    hass.states.async_set("light.kitchen", "on")
    hass.states.async_set("cover.garage", "open", {"device_class": "garage"})

    await client.send_json_auto_id(
        {"type": "cloud/google_assistant/entities/get", "entity_id": "light.kitchen"}
    )
    response = await client.receive_json()

    assert response["success"]
    assert response["result"] == {
        "disable_2fa": None,
        "entity_id": "light.kitchen",
        "might_2fa": False,
        "traits": ["action.devices.traits.OnOff"],
    }

    await client.send_json_auto_id(
        {"type": "cloud/google_assistant/entities/get", "entity_id": "cover.garage"}
    )
    response = await client.receive_json()

    assert response["success"]
    assert response["result"] == {
        "disable_2fa": None,
        "entity_id": "cover.garage",
        "might_2fa": True,
        "traits": ["action.devices.traits.OpenClose"],
    }

    # Set the disable 2fa flag
    await client.send_json_auto_id(
        {
            "type": "cloud/google_assistant/entities/update",
            "entity_id": "cover.garage",
            "disable_2fa": True,
        }
    )
    response = await client.receive_json()

    assert response["success"]

    await client.send_json_auto_id(
        {"type": "cloud/google_assistant/entities/get", "entity_id": "cover.garage"}
    )
    response = await client.receive_json()

    assert response["success"]
    assert response["result"] == {
        "disable_2fa": True,
        "entity_id": "cover.garage",
        "might_2fa": True,
        "traits": ["action.devices.traits.OpenClose"],
    }