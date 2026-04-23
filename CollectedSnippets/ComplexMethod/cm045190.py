async def test_mcp_workbench_serialization_with_overrides(sample_server_params: StdioServerParams) -> None:
    """Test that McpWorkbench can be serialized and deserialized with overrides."""

    overrides: Dict[str, ToolOverride] = {
        "fetch": ToolOverride(name="web_fetch", description="Enhanced web fetching tool")
    }

    # Create workbench with overrides
    workbench = McpWorkbench(server_params=sample_server_params, tool_overrides=overrides)

    # Save configuration
    config = workbench.dump_component()
    assert "tool_overrides" in config.config
    assert "fetch" in config.config["tool_overrides"]
    assert config.config["tool_overrides"]["fetch"]["name"] == "web_fetch"
    assert config.config["tool_overrides"]["fetch"]["description"] == "Enhanced web fetching tool"

    # Load workbench from configuration
    new_workbench = McpWorkbench.load_component(config)
    assert len(new_workbench._tool_overrides) == 1  # type: ignore[reportPrivateUsage]
    assert new_workbench._tool_overrides["fetch"].name == "web_fetch"  # type: ignore[reportPrivateUsage]
    assert new_workbench._tool_overrides["fetch"].description == "Enhanced web fetching tool"