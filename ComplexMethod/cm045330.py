async def test_static_workbench_serialization_with_overrides() -> None:
    """Test that StaticWorkbench can be serialized and deserialized with overrides."""

    def test_tool_func(x: Annotated[int, "The number to double."]) -> int:
        return x * 2

    test_tool = FunctionTool(
        test_tool_func,
        name="double",
        description="A test tool that doubles a number.",
        global_imports=[ImportFromModule(module="typing_extensions", imports=["Annotated"])],
    )

    overrides: Dict[str, ToolOverride] = {
        "double": ToolOverride(name="multiply_by_two", description="Multiplies a number by 2")
    }

    # Create workbench with overrides
    workbench = StaticWorkbench(tools=[test_tool], tool_overrides=overrides)

    # Save configuration
    config = workbench.dump_component()
    assert "tool_overrides" in config.config

    # Load workbench from configuration
    async with Workbench.load_component(config) as new_workbench:
        tools = await new_workbench.list_tools()
        assert len(tools) == 1
        assert tools[0]["name"] == "multiply_by_two"
        assert tools[0].get("description") == "Multiplies a number by 2"

        # Test calling tool with override name
        result = await new_workbench.call_tool("multiply_by_two", {"x": 5})
        assert result.name == "multiply_by_two"
        assert result.result[0].content == "10"
        assert result.is_error is False