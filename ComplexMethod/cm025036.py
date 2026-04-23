async def test_last_step(hass: HomeAssistant) -> None:
    """Test SchemaFlowFormStep with schema set to None."""

    async def _step2_next_step(_: dict[str, Any]) -> str:
        return "step3"

    CONFIG_FLOW: dict[str, SchemaFlowFormStep | SchemaFlowMenuStep] = {
        "user": SchemaFlowFormStep(next_step="step1"),
        "step1": SchemaFlowFormStep(vol.Schema({}), next_step="step2"),
        "step2": SchemaFlowFormStep(vol.Schema({}), next_step=_step2_next_step),
        "step3": SchemaFlowFormStep(vol.Schema({}), next_step=None),
    }

    class TestConfigFlow(MockSchemaConfigFlowHandler, domain=TEST_DOMAIN):
        """Handle a config or options flow for Derivative."""

        config_flow = CONFIG_FLOW

    mock_platform(hass, f"{TEST_DOMAIN}.config_flow")
    with patch.dict(config_entries.HANDLERS, {TEST_DOMAIN: TestConfigFlow}):
        result = await hass.config_entries.flow.async_init(
            TEST_DOMAIN, context={"source": "user"}
        )
        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "step1"
        assert result["last_step"] is False

        result = await hass.config_entries.flow.async_configure(result["flow_id"], {})
        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "step2"
        assert result["last_step"] is None

        result = await hass.config_entries.flow.async_configure(result["flow_id"], {})
        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "step3"
        assert result["last_step"] is True

        result = await hass.config_entries.flow.async_configure(result["flow_id"], {})
        assert result["type"] is FlowResultType.CREATE_ENTRY