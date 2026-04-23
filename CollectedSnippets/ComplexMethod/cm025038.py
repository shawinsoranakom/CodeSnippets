async def test_options_flow_state(hass: HomeAssistant) -> None:
    """Test flow_state handling in SchemaFlowFormStep."""

    OPTIONS_SCHEMA = vol.Schema(
        {vol.Optional("option1", default="a very reasonable default"): str}
    )

    async def _init_schema(handler: SchemaCommonFlowHandler) -> None:
        handler.flow_state["idx"] = None

    async def _validate_step1_input(
        handler: SchemaCommonFlowHandler, user_input: dict[str, Any]
    ) -> dict[str, Any]:
        handler.flow_state["idx"] = user_input["option1"]
        return user_input

    async def _validate_step2_input(
        handler: SchemaCommonFlowHandler, user_input: dict[str, Any]
    ) -> dict[str, Any]:
        user_input["idx_from_flow_state"] = handler.flow_state["idx"]
        return user_input

    OPTIONS_FLOW: dict[str, SchemaFlowFormStep | SchemaFlowMenuStep] = {
        "init": SchemaFlowFormStep(_init_schema, next_step="step_1"),
        "step_1": SchemaFlowFormStep(
            OPTIONS_SCHEMA,
            validate_user_input=_validate_step1_input,
            next_step="step_2",
        ),
        "step_2": SchemaFlowFormStep(
            OPTIONS_SCHEMA,
            validate_user_input=_validate_step2_input,
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

    # Start flow in basic mode, flow state is initialised with None value
    result = await hass.config_entries.options.async_init(config_entry.entry_id)
    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert result["step_id"] == "step_1"

    options_handler: SchemaOptionsFlowHandler
    options_handler = hass.config_entries.options._progress[result["flow_id"]]
    assert options_handler._common_handler.flow_state == {"idx": None}

    # Ensure that self.options and self._common_handler.options refer to the
    # same mutable copy of the options
    assert options_handler.options is options_handler._common_handler.options

    # In step 1, flow state is updated with user input
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {"option1": "blublu"}
    )
    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert result["step_id"] == "step_2"

    options_handler = hass.config_entries.options._progress[result["flow_id"]]
    assert options_handler._common_handler.flow_state == {"idx": "blublu"}

    # In step 2, options were updated from flow state
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {"option1": "blabla"}
    )
    assert result["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY
    assert result["data"] == {
        "idx_from_flow_state": "blublu",
        "option1": "blabla",
    }