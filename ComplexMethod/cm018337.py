async def test_lcn_entities_add_command(
    hass: HomeAssistant, hass_ws_client: WebSocketGenerator, entry: MockConfigEntry
) -> None:
    """Test lcn/entities/add command."""
    await init_integration(hass, entry)

    client = await hass_ws_client(hass)

    entity_config = {
        key: ENTITIES_ADD_PAYLOAD[key]
        for key in (CONF_ADDRESS, CONF_NAME, CONF_DOMAIN, CONF_DOMAIN_DATA)
    }

    assert entity_config not in entry.data[CONF_ENTITIES]

    await client.send_json_auto_id({**ENTITIES_ADD_PAYLOAD, "entry_id": entry.entry_id})

    res = await client.receive_json()
    assert res["success"], res

    assert entity_config in entry.data[CONF_ENTITIES]

    # invalid domain
    await client.send_json_auto_id(
        {**ENTITIES_ADD_PAYLOAD, "entry_id": entry.entry_id, CONF_DOMAIN: "invalid"}
    )

    res = await client.receive_json()
    assert not res["success"]
    assert res["error"]["code"] == "home_assistant_error"
    assert res["error"]["translation_key"] == "invalid_domain"