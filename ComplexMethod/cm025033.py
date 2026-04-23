async def test_config_flow_advanced_option(
    hass: HomeAssistant, manager: data_entry_flow.FlowManager, marker
) -> None:
    """Test handling of advanced options in config flow."""
    manager.hass = hass

    CONFIG_SCHEMA = vol.Schema(
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

    CONFIG_FLOW: dict[str, SchemaFlowFormStep | SchemaFlowMenuStep] = {
        "init": SchemaFlowFormStep(CONFIG_SCHEMA)
    }

    @manager.mock_reg_handler("test")
    class TestFlow(MockSchemaConfigFlowHandler):
        config_flow = CONFIG_FLOW

    # Start flow in basic mode
    result = await manager.async_init("test")
    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert list(result["data_schema"].schema.keys()) == ["option1"]

    result = await manager.async_configure(result["flow_id"], {"option1": "blabla"})
    assert result["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY
    assert result["data"] == {}
    assert result["options"] == {
        "advanced_default": "a very reasonable default",
        "option1": "blabla",
    }
    for option in result["options"]:
        # Make sure we didn't get the Optional or Required instance as key
        assert isinstance(option, str)

    # Start flow in advanced mode
    result = await manager.async_init("test", context={"show_advanced_options": True})
    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert list(result["data_schema"].schema.keys()) == [
        "option1",
        "advanced_no_default",
        "advanced_default",
    ]

    result = await manager.async_configure(
        result["flow_id"], {"advanced_no_default": "abc123", "option1": "blabla"}
    )
    assert result["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY
    assert result["data"] == {}
    assert result["options"] == {
        "advanced_default": "a very reasonable default",
        "advanced_no_default": "abc123",
        "option1": "blabla",
    }
    for option in result["options"]:
        # Make sure we didn't get the Optional or Required instance as key
        assert isinstance(option, str)

    # Start flow in advanced mode
    result = await manager.async_init("test", context={"show_advanced_options": True})
    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert list(result["data_schema"].schema.keys()) == [
        "option1",
        "advanced_no_default",
        "advanced_default",
    ]

    result = await manager.async_configure(
        result["flow_id"],
        {
            "advanced_default": "not default",
            "advanced_no_default": "abc123",
            "option1": "blabla",
        },
    )
    assert result["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY
    assert result["data"] == {}
    assert result["options"] == {
        "advanced_default": "not default",
        "advanced_no_default": "abc123",
        "option1": "blabla",
    }
    for option in result["options"]:
        # Make sure we didn't get the Optional or Required instance as key
        assert isinstance(option, str)