async def test_update(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    hass_ws_client: WebSocketGenerator,
    storage_setup,
) -> None:
    """Test updating min/max updates the state."""

    assert await storage_setup()

    input_id = "from_storage"
    input_entity_id = f"{DOMAIN}.{input_id}"

    state = hass.states.get(input_entity_id)
    assert state.attributes[ATTR_FRIENDLY_NAME] == "from storage"
    assert state.attributes[ATTR_MODE] == MODE_TEXT
    assert state.state == "loaded from storage"
    assert entity_registry.async_get_entity_id(DOMAIN, DOMAIN, input_id) is not None

    client = await hass_ws_client(hass)

    updated_settings = {
        ATTR_NAME: "even newer name",
        CONF_INITIAL: "newer option",
        ATTR_MAX: TEST_VAL_MAX,
        ATTR_MIN: 6,
        ATTR_MODE: "password",
    }
    await client.send_json(
        {
            "id": 6,
            "type": f"{DOMAIN}/update",
            f"{DOMAIN}_id": f"{input_id}",
            **updated_settings,
        }
    )
    resp = await client.receive_json()
    assert resp["success"]
    assert resp["result"] == {"id": "from_storage"} | updated_settings

    state = hass.states.get(input_entity_id)
    assert state.state == "loaded from storage"
    assert state.attributes[ATTR_FRIENDLY_NAME] == "even newer name"
    assert state.attributes[ATTR_MODE] == "password"
    assert state.attributes[ATTR_MIN] == 6
    assert state.attributes[ATTR_MAX] == TEST_VAL_MAX