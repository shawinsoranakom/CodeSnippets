async def test_options_flow_omit_optional_keys(
    hass: HomeAssistant, manager: data_entry_flow.FlowManager
) -> None:
    """Test handling of advanced options in options flow."""
    manager.hass = hass

    OPTIONS_SCHEMA = vol.Schema(
        {
            vol.Optional("optional_no_default"): str,
            vol.Optional("optional_default", default="a very reasonable default"): str,
            vol.Optional("advanced_no_default", description={"advanced": True}): str,
            vol.Optional(
                "advanced_default",
                default="a very reasonable default",
                description={"advanced": True},
            ): str,
        }
    )

    OPTIONS_FLOW: dict[str, SchemaFlowFormStep | SchemaFlowMenuStep] = {
        "init": SchemaFlowFormStep(OPTIONS_SCHEMA)
    }

    class TestFlow(MockSchemaConfigFlowHandler, domain="test"):
        config_flow = {}
        options_flow = OPTIONS_FLOW

    mock_integration(hass, MockModule("test"))
    mock_platform(hass, "test.config_flow", None)
    config_entry = MockConfigEntry(
        data={},
        domain="test",
        options={
            "optional_no_default": "abc123",
            "optional_default": "not default",
            "advanced_no_default": "abc123",
            "advanced_default": "not default",
        },
    )
    config_entry.add_to_hass(hass)

    # Start flow in basic mode
    result = await hass.config_entries.options.async_init(config_entry.entry_id)
    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert list(result["data_schema"].schema.keys()) == [
        "optional_no_default",
        "optional_default",
    ]

    result = await hass.config_entries.options.async_configure(result["flow_id"], {})
    assert result["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY
    assert result["data"] == {
        "advanced_default": "not default",
        "advanced_no_default": "abc123",
        "optional_default": "a very reasonable default",
    }

    # Start flow in advanced mode
    result = await hass.config_entries.options.async_init(
        config_entry.entry_id, context={"show_advanced_options": True}
    )
    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert list(result["data_schema"].schema.keys()) == [
        "optional_no_default",
        "optional_default",
        "advanced_no_default",
        "advanced_default",
    ]

    result = await hass.config_entries.options.async_configure(result["flow_id"], {})
    assert result["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY
    assert result["data"] == {
        "advanced_default": "a very reasonable default",
        "optional_default": "a very reasonable default",
    }