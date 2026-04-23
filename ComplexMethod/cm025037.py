async def test_suggested_values(
    hass: HomeAssistant, manager: data_entry_flow.FlowManager
) -> None:
    """Test suggested_values handling in SchemaFlowFormStep."""
    manager.hass = hass

    OPTIONS_SCHEMA = vol.Schema(
        {vol.Optional("option1", default="a very reasonable default"): str}
    )

    async def _validate_user_input(
        handler: SchemaCommonFlowHandler, user_input: dict[str, Any]
    ) -> dict[str, Any]:
        if user_input["option1"] == "not a valid value":
            raise SchemaFlowError("option1 not using a valid value")
        return user_input

    async def _step_2_suggested_values(_: SchemaCommonFlowHandler) -> dict[str, Any]:
        return {"option1": "a random override"}

    OPTIONS_FLOW: dict[str, SchemaFlowFormStep | SchemaFlowMenuStep] = {
        "init": SchemaFlowFormStep(OPTIONS_SCHEMA, next_step="step_1"),
        "step_1": SchemaFlowFormStep(OPTIONS_SCHEMA, next_step="step_2"),
        "step_2": SchemaFlowFormStep(
            OPTIONS_SCHEMA,
            suggested_values=_step_2_suggested_values,
            next_step="step_3",
        ),
        "step_3": SchemaFlowFormStep(
            OPTIONS_SCHEMA, suggested_values=None, next_step="step_4"
        ),
        "step_4": SchemaFlowFormStep(
            OPTIONS_SCHEMA, validate_user_input=_validate_user_input
        ),
    }

    class TestFlow(MockSchemaConfigFlowHandler, domain="test"):
        config_flow = {}
        options_flow = OPTIONS_FLOW

    mock_integration(hass, MockModule("test"))
    mock_platform(hass, "test.config_flow", None)
    config_entry = MockConfigEntry(
        data={},
        domain="test",
        options={"option1": "initial value"},
    )
    config_entry.add_to_hass(hass)

    # Start flow in basic mode, suggested values should be the existing options
    result = await hass.config_entries.options.async_init(config_entry.entry_id)
    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert result["step_id"] == "init"
    schema_keys: list[vol.Optional] = list(result["data_schema"].schema.keys())
    assert schema_keys == ["option1"]
    assert schema_keys[0].description == {"suggested_value": "initial value"}

    # Go to step 1, suggested values should be the input from init
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {"option1": "blublu"}
    )
    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert result["step_id"] == "step_1"
    schema_keys: list[vol.Optional] = list(result["data_schema"].schema.keys())
    assert schema_keys == ["option1"]
    assert schema_keys[0].description == {"suggested_value": "blublu"}

    # Go to step 2, suggested values should come from the callback function
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {"option1": "blabla"}
    )
    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert result["step_id"] == "step_2"
    schema_keys: list[vol.Optional] = list(result["data_schema"].schema.keys())
    assert schema_keys == ["option1"]
    assert schema_keys[0].description == {"suggested_value": "a random override"}

    # Go to step 3, suggested values should be empty
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {"option1": "blabla"}
    )
    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert result["step_id"] == "step_3"
    schema_keys: list[vol.Optional] = list(result["data_schema"].schema.keys())
    assert schema_keys == ["option1"]
    assert schema_keys[0].description is None

    # Go to step 4, suggested values should be the user input
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {"option1": "blabla"}
    )
    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert result["step_id"] == "step_4"
    schema_keys: list[vol.Optional] = list(result["data_schema"].schema.keys())
    assert schema_keys == ["option1"]
    assert schema_keys[0].description == {"suggested_value": "blabla"}

    # Incorrect value in step 4, suggested values should be the user input
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {"option1": "not a valid value"}
    )
    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert result["step_id"] == "step_4"
    schema_keys: list[vol.Optional] = list(result["data_schema"].schema.keys())
    assert schema_keys == ["option1"]
    assert schema_keys[0].description == {"suggested_value": "not a valid value"}

    # Correct value in step 4, end of flow
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {"option1": "blabla"}
    )
    assert result["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY