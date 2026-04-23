async def test_config_flow_preview(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    template_type: str,
    state_template: str,
    extra_user_input: dict[str, Any],
    input_states: dict[str, Any],
    template_states: str,
    extra_attributes: list[dict[str, Any]],
    listeners: list[list[str]],
) -> None:
    """Test the config flow preview."""
    client = await hass_ws_client(hass)

    hass.states.async_set("binary_sensor.available", "on")
    await hass.async_block_till_done()

    input_entities = ["one", "two"]

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

    availability = {
        "advanced_options": {
            "availability": "{{ is_state('binary_sensor.available', 'on') }}"
        }
    }

    await client.send_json_auto_id(
        {
            "type": "template/start_preview",
            "flow_id": result["flow_id"],
            "flow_type": "config_flow",
            "user_input": {
                "name": "My template",
                "state": state_template,
                **availability,
            }
            | extra_user_input,
        }
    )
    msg = await client.receive_json()
    assert msg["success"]
    assert msg["result"] is None

    entities = [f"{template_type}.{_id}" for _id in listeners[0]]
    entities.append("binary_sensor.available")

    msg = await client.receive_json()
    assert msg["event"] == {
        "attributes": {"friendly_name": "My template"} | extra_attributes[0],
        "listeners": {
            "all": False,
            "domains": [],
            "entities": unordered(entities),
            "time": False,
        },
        "state": template_states[0],
    }

    for input_entity in input_entities:
        hass.states.async_set(
            f"{template_type}.{input_entity}", input_states[input_entity], {}
        )
        await hass.async_block_till_done()

    entities = [f"{template_type}.{_id}" for _id in listeners[1]]
    entities.append("binary_sensor.available")

    for template_state in template_states[1:]:
        msg = await client.receive_json()
        assert msg["event"] == {
            "attributes": {"friendly_name": "My template"}
            | extra_attributes[0]
            | extra_attributes[1],
            "listeners": {
                "all": False,
                "domains": [],
                "entities": unordered(entities),
                "time": False,
            },
            "state": template_state,
        }
    assert len(hass.states.async_all()) == 3

    # Test preview availability.
    hass.states.async_set("binary_sensor.available", "off")
    await hass.async_block_till_done()

    msg = await client.receive_json()
    assert msg["event"] == {
        "attributes": {"friendly_name": "My template"}
        | extra_attributes[0]
        | extra_attributes[1],
        "listeners": {
            "all": False,
            "domains": [],
            "entities": unordered(entities),
            "time": False,
        },
        "state": STATE_UNAVAILABLE,
    }

    assert len(hass.states.async_all()) == 3