async def test_options_flow_advanced_option(
    hass: HomeAssistant, manager: data_entry_flow.FlowManager, marker
) -> None:
    """Test handling of advanced options in options flow."""
    manager.hass = hass

    OPTIONS_SCHEMA = vol.Schema(
        {
            marker("option1"): str,
            marker("advanced_no_default", description={"advanced": True}): str,
            marker(
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
            "option1": "blabla",
            "advanced_no_default": "abc123",
            "advanced_default": "not default",
        },
    )
    config_entry.add_to_hass(hass)

    # Start flow in basic mode
    result = await hass.config_entries.options.async_init(config_entry.entry_id)
    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert list(result["data_schema"].schema.keys()) == ["option1"]

    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {"option1": "blublu"}
    )
    assert result["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY
    assert result["data"] == {
        "advanced_default": "not default",
        "advanced_no_default": "abc123",
        "option1": "blublu",
    }
    for option in result["data"]:
        # Make sure we didn't get the Optional or Required instance as key
        assert isinstance(option, str)

    # Start flow in advanced mode
    result = await hass.config_entries.options.async_init(
        config_entry.entry_id, context={"show_advanced_options": True}
    )
    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert list(result["data_schema"].schema.keys()) == [
        "option1",
        "advanced_no_default",
        "advanced_default",
    ]

    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {"advanced_no_default": "def456", "option1": "blabla"}
    )
    assert result["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY
    assert result["data"] == {
        "advanced_default": "a very reasonable default",
        "advanced_no_default": "def456",
        "option1": "blabla",
    }
    for option in result["data"]:
        # Make sure we didn't get the Optional or Required instance as key
        assert isinstance(option, str)

    # Start flow in advanced mode
    result = await hass.config_entries.options.async_init(
        config_entry.entry_id, context={"show_advanced_options": True}
    )
    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert list(result["data_schema"].schema.keys()) == [
        "option1",
        "advanced_no_default",
        "advanced_default",
    ]

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {
            "advanced_default": "also not default",
            "advanced_no_default": "abc123",
            "option1": "blabla",
        },
    )
    assert result["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY
    assert result["data"] == {
        "advanced_default": "also not default",
        "advanced_no_default": "abc123",
        "option1": "blabla",
    }
    for option in result["data"]:
        # Make sure we didn't get the Optional or Required instance as key
        assert isinstance(option, str)