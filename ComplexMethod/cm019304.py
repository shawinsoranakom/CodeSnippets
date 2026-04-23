async def test_config_flow_preview(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    domain: str,
    extra_user_input: dict[str, Any],
    input_states: list[str],
    group_state: str,
    extra_attributes: list[dict[str, Any]],
) -> None:
    """Test the config flow preview."""
    client = await hass_ws_client(hass)

    input_entities = [f"{domain}.input_one", f"{domain}.input_two"]

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.MENU

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"next_step_id": domain},
    )
    await hass.async_block_till_done()
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == domain
    assert result["errors"] is None
    assert result["preview"] == "group"

    await client.send_json_auto_id(
        {
            "type": "group/start_preview",
            "flow_id": result["flow_id"],
            "flow_type": "config_flow",
            "user_input": {"name": "My group", "entities": input_entities}
            | extra_user_input,
        }
    )
    msg = await client.receive_json()
    preview_subscribe_id = msg["id"]
    assert msg["success"]
    assert msg["result"] is None

    msg = await client.receive_json()
    assert msg["event"] == {
        "attributes": {"friendly_name": "My group"} | extra_attributes[0],
        "state": "unavailable",
    }

    await client.send_json_auto_id(
        {
            "type": "unsubscribe_events",
            "subscription": preview_subscribe_id,
        }
    )
    msg = await client.receive_json()
    assert msg["success"]

    hass.states.async_set(input_entities[0], input_states[0])
    hass.states.async_set(input_entities[1], input_states[1])

    await client.send_json_auto_id(
        {
            "type": "group/start_preview",
            "flow_id": result["flow_id"],
            "flow_type": "config_flow",
            "user_input": {"name": "My group", "entities": input_entities}
            | extra_user_input,
        }
    )
    msg = await client.receive_json()
    preview_subscribe_id = msg["id"]
    assert msg["success"]
    assert msg["result"] is None

    msg = await client.receive_json()
    assert msg["event"] == {
        "attributes": {
            "entity_id": input_entities,
            "friendly_name": "My group",
        }
        | extra_attributes[0]
        | extra_attributes[1],
        "state": group_state,
    }
    assert len(hass.states.async_all()) == 2