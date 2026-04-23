async def test_option_flow_preview(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    domain: str,
    extra_config_flow_data: dict[str, Any],
    extra_user_input: dict[str, Any],
    input_states: list[str],
    group_state: str,
    extra_attributes: dict[str, Any],
) -> None:
    """Test the option flow preview."""
    input_entities = [f"{domain}.input_one", f"{domain}.input_two"]

    # Setup the config entry
    config_entry = MockConfigEntry(
        data={},
        domain=DOMAIN,
        options={
            "entities": input_entities,
            "group_type": domain,
            "hide_members": False,
            "name": "My group",
        }
        | extra_config_flow_data,
        title="My group",
    )
    config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    client = await hass_ws_client(hass)

    result = await hass.config_entries.options.async_init(config_entry.entry_id)
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] is None
    assert result["preview"] == "group"

    hass.states.async_set(input_entities[0], input_states[0])
    hass.states.async_set(input_entities[1], input_states[1])

    await client.send_json_auto_id(
        {
            "type": "group/start_preview",
            "flow_id": result["flow_id"],
            "flow_type": "options_flow",
            "user_input": {"entities": input_entities} | extra_user_input,
        }
    )
    msg = await client.receive_json()
    assert msg["success"]
    assert msg["result"] is None

    msg = await client.receive_json()
    assert msg["event"] == {
        "attributes": {"entity_id": input_entities, "friendly_name": "My group"}
        | extra_attributes[0]
        | extra_attributes[1],
        "state": group_state,
    }
    assert len(hass.states.async_all()) == 3