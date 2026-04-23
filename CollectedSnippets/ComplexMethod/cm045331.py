async def test_static_workbench_partial_overrides() -> None:
    """Test StaticWorkbench with partial overrides (name only, description only)."""

    def tool1_func(x: Annotated[int, "Number"]) -> int:
        return x

    def tool2_func(x: Annotated[int, "Number"]) -> int:
        return x

    tool1 = FunctionTool(
        tool1_func,
        name="tool1",
        description="Original description 1",
        global_imports=[ImportFromModule(module="typing_extensions", imports=["Annotated"])],
    )
    tool2 = FunctionTool(
        tool2_func,
        name="tool2",
        description="Original description 2",
        global_imports=[ImportFromModule(module="typing_extensions", imports=["Annotated"])],
    )

    overrides: Dict[str, ToolOverride] = {
        "tool1": ToolOverride(name="renamed_tool1"),  # Only name override
        "tool2": ToolOverride(description="New description 2"),  # Only description override
    }

    async with StaticWorkbench(tools=[tool1, tool2], tool_overrides=overrides) as workbench:
        tools = await workbench.list_tools()

        # tool1: name overridden, description unchanged
        assert tools[0].get("name") == "renamed_tool1"
        assert tools[0].get("description") == "Original description 1"

        # tool2: name unchanged, description overridden
        assert tools[1].get("name") == "tool2"
        assert tools[1].get("description") == "New description 2"

        # Test calling with override name
        result1 = await workbench.call_tool("renamed_tool1", {"x": 42})
        assert result1.name == "renamed_tool1"
        assert result1.result[0].content == "42"

        # Test calling with original name
        result2 = await workbench.call_tool("tool2", {"x": 42})
        assert result2.name == "tool2"
        assert result2.result[0].content == "42"