async def test_menu_step(hass: HomeAssistant) -> None:
    """Test menu step."""

    MENU_1 = ["option1", "option2"]

    async def menu_2(handler: SchemaCommonFlowHandler) -> list[str]:
        return ["option3", "option4"]

    async def _option1_next_step(_: dict[str, Any]) -> str:
        return "menu2"

    CONFIG_FLOW: dict[str, SchemaFlowFormStep | SchemaFlowMenuStep] = {
        "user": SchemaFlowMenuStep(MENU_1),
        "option1": SchemaFlowFormStep(vol.Schema({}), next_step=_option1_next_step),
        "menu2": SchemaFlowMenuStep(menu_2),
        "option3": SchemaFlowFormStep(vol.Schema({}), next_step="option4"),
        "option4": SchemaFlowFormStep(vol.Schema({})),
    }

    class TestConfigFlow(MockSchemaConfigFlowHandler, domain=TEST_DOMAIN):
        """Handle a config or options flow for Derivative."""

        config_flow = CONFIG_FLOW

    mock_platform(hass, f"{TEST_DOMAIN}.config_flow")
    with patch.dict(config_entries.HANDLERS, {TEST_DOMAIN: TestConfigFlow}):
        result = await hass.config_entries.flow.async_init(
            TEST_DOMAIN, context={"source": "user"}
        )
        assert result["type"] is FlowResultType.MENU
        assert result["step_id"] == "user"

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"next_step_id": "option1"},
        )
        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "option1"

        result = await hass.config_entries.flow.async_configure(result["flow_id"], {})
        assert result["type"] is FlowResultType.MENU
        assert result["step_id"] == "menu2"

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"next_step_id": "option3"},
        )
        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "option3"

        result = await hass.config_entries.flow.async_configure(result["flow_id"], {})
        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "option4"

        result = await hass.config_entries.flow.async_configure(result["flow_id"], {})
        assert result["type"] is FlowResultType.CREATE_ENTRY