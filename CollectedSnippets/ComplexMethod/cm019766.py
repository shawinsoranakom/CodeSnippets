async def test_update(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    hass_ws_client: WebSocketGenerator,
    storage_setup,
) -> None:
    """Test updating timer entity."""

    assert await storage_setup()

    timer_id = "from_storage"
    timer_entity_id = f"{DOMAIN}.{DOMAIN}_{timer_id}"

    state = hass.states.get(timer_entity_id)
    assert state.state == STATUS_IDLE
    assert state.attributes == {
        ATTR_DURATION: "0:00:00",
        ATTR_EDITABLE: True,
        ATTR_FRIENDLY_NAME: "timer from storage",
    }
    assert (
        entity_registry.async_get_entity_id(DOMAIN, DOMAIN, timer_id) == timer_entity_id
    )

    client = await hass_ws_client(hass)

    updated_settings = {
        CONF_NAME: "timer from storage",
        CONF_DURATION: 33,
        CONF_RESTORE: True,
    }
    await client.send_json(
        {
            "id": 6,
            "type": f"{DOMAIN}/update",
            f"{DOMAIN}_id": f"{timer_id}",
            **updated_settings,
        }
    )
    resp = await client.receive_json()
    assert resp["success"]
    assert resp["result"] == {
        "id": "from_storage",
        CONF_DURATION: "0:00:33",
        CONF_NAME: "timer from storage",
        CONF_RESTORE: True,
    }

    state = hass.states.get(timer_entity_id)
    assert state.state == STATUS_IDLE
    assert state.attributes == {
        ATTR_DURATION: "0:00:33",
        ATTR_EDITABLE: True,
        ATTR_FRIENDLY_NAME: "timer from storage",
        ATTR_RESTORE: True,
    }