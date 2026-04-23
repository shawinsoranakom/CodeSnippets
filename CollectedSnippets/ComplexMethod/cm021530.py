async def test_config_flow_preview_template_error(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    template_type: str,
    state_template: str,
    input_states: list[dict[str, str]],
    template_states: list[str],
    error_events: list[str],
) -> None:
    """Test the config flow preview."""
    client = await hass_ws_client(hass)

    input_entities = ["one", "two"]

    for input_entity in input_entities:
        hass.states.async_set(
            f"{template_type}.{input_entity}", input_states[0][input_entity], {}
        )

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.MENU

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"next_step_id": template_type},
    )
    await hass.async_block_till_done()
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == template_type
    assert result["errors"] is None
    assert result["preview"] == "template"

    await client.send_json_auto_id(
        {
            "type": "template/start_preview",
            "flow_id": result["flow_id"],
            "flow_type": "config_flow",
            "user_input": {"name": "My template", "state": state_template},
        }
    )
    msg = await client.receive_json()
    assert msg["type"] == "result"
    assert msg["success"]

    msg = await client.receive_json()
    assert msg["type"] == "event"
    assert msg["event"]["state"] == template_states[0]

    for input_entity in input_entities:
        hass.states.async_set(
            f"{template_type}.{input_entity}", input_states[1][input_entity], {}
        )

    for error_event in error_events:
        msg = await client.receive_json()
        assert msg["type"] == "event"
        assert msg["event"] == {"error": error_event}