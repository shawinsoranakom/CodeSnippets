async def test_option_flow_preview(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    template_type: str,
    old_state_template: str,
    new_state_template: str,
    extra_config_flow_data: dict[str, Any],
    extra_user_input: dict[str, Any],
    input_states: dict[str, Any],
    template_state: str,
    extra_attributes: dict[str, Any],
    listeners: list[str],
) -> None:
    """Test the option flow preview."""
    client = await hass_ws_client(hass)

    input_entities = ["one", "two"]

    # Setup the config entry
    config_entry = MockConfigEntry(
        data={},
        domain=DOMAIN,
        options={
            "name": "My template",
            "state": old_state_template,
            "template_type": template_type,
        }
        | extra_config_flow_data,
        title="My template",
    )
    config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    result = await hass.config_entries.options.async_init(config_entry.entry_id)
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] is None
    assert result["preview"] == "template"

    for input_entity in input_entities:
        hass.states.async_set(
            f"{template_type}.{input_entity}", input_states[input_entity], {}
        )

    await client.send_json_auto_id(
        {
            "type": "template/start_preview",
            "flow_id": result["flow_id"],
            "flow_type": "options_flow",
            "user_input": {"state": new_state_template} | extra_user_input,
        }
    )
    msg = await client.receive_json()
    assert msg["success"]
    assert msg["result"] is None

    msg = await client.receive_json()
    assert msg["event"] == {
        "attributes": {"friendly_name": "My template"} | extra_attributes,
        "listeners": {
            "all": False,
            "domains": [],
            "entities": unordered([f"{template_type}.{_id}" for _id in listeners]),
            "time": False,
        },
        "state": template_state,
    }
    assert len(hass.states.async_all()) == 3