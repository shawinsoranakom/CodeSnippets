async def test_ws_create_duplicates(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    hass_ws_client: WebSocketGenerator,
    storage_setup,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test create WS with duplicates."""
    assert await storage_setup(items=[])

    input_id = "new_input"
    input_entity_id = f"{DOMAIN}.{input_id}"

    state = hass.states.get(input_entity_id)
    assert state is None
    assert entity_registry.async_get_entity_id(DOMAIN, DOMAIN, input_id) is None

    client = await hass_ws_client(hass)

    await client.send_json(
        {
            "id": 6,
            "type": f"{DOMAIN}/create",
            "name": "New Input",
            "options": ["new option", "even newer option", "even newer option"],
            "initial": "even newer option",
        }
    )
    resp = await client.receive_json()
    assert not resp["success"]
    assert resp["error"]["code"] == "home_assistant_error"
    assert resp["error"]["message"] == "Duplicate options are not allowed"

    assert not hass.states.get(input_entity_id)