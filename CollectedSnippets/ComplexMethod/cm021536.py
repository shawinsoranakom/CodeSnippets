async def test_preview_this_variable_options_flow(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    template_type: str,
    extra_config: dict,
    set_state: str,
    expected_state: str,
) -> None:
    """Test 'this' variable with options flow."""
    client = await hass_ws_client(hass)

    config_entry = MockConfigEntry(
        data={},
        domain=DOMAIN,
        options={
            "name": "My template",
            "template_type": template_type,
            "state": "{{ None }}",
            **extra_config,
        },
        title="My template",
    )
    config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    entity_id = f"{template_type}.my_template"
    hass.states.async_set(entity_id, set_state)
    await hass.async_block_till_done()

    state = hass.states.get(f"{template_type}.my_template")
    assert state.state == expected_state

    result = await hass.config_entries.options.async_init(config_entry.entry_id)
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] is None
    assert result["preview"] == "template"

    await client.send_json_auto_id(
        {
            "type": "template/start_preview",
            "flow_id": result["flow_id"],
            "flow_type": "options_flow",
            "user_input": {
                "state": "{{ this.state }}",
                **extra_config,
            },
        }
    )
    msg = await client.receive_json()
    assert msg["success"]
    assert msg["result"] is None

    msg = await client.receive_json()
    assert msg["event"]["state"] == expected_state