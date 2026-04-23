async def test_static_workbench_with_tool_overrides() -> None:
    """Test StaticWorkbench with tool name and description overrides."""

    def test_tool_func_1(x: Annotated[int, "The number to double."]) -> int:
        return x * 2

    def test_tool_func_2(a: Annotated[int, "First number"], b: Annotated[int, "Second number"]) -> int:
        return a + b

    test_tool_1 = FunctionTool(
        test_tool_func_1,
        name="double",
        description="A test tool that doubles a number.",
        global_imports=[ImportFromModule(module="typing_extensions", imports=["Annotated"])],
    )
    test_tool_2 = FunctionTool(
        test_tool_func_2,
        name="add",
        description="A test tool that adds two numbers.",
        global_imports=[ImportFromModule(module="typing_extensions", imports=["Annotated"])],
    )

    # Define tool overrides
    overrides: Dict[str, ToolOverride] = {
        "double": ToolOverride(name="multiply_by_two", description="Multiplies a number by 2"),
        "add": ToolOverride(description="Performs addition of two integers"),  # Only override description
    }

    # Create a StaticWorkbench instance with tool overrides
    async with StaticWorkbench(tools=[test_tool_1, test_tool_2], tool_overrides=overrides) as workbench:
        # List tools and verify overrides are applied
        tools = await workbench.list_tools()
        assert len(tools) == 2

        # Check first tool has name and description overridden
        assert tools[0]["name"] == "multiply_by_two"
        assert tools[0].get("description") == "Multiplies a number by 2"
        assert tools[0].get("parameters") == {
            "type": "object",
            "properties": {"x": {"type": "integer", "title": "X", "description": "The number to double."}},
            "required": ["x"],
            "additionalProperties": False,
        }

        # Check second tool has only description overridden
        assert tools[1]["name"] == "add"  # Original name
        assert tools[1].get("description") == "Performs addition of two integers"  # Overridden description
        assert tools[1].get("parameters") == {
            "type": "object",
            "properties": {
                "a": {"type": "integer", "title": "A", "description": "First number"},
                "b": {"type": "integer", "title": "B", "description": "Second number"},
            },
            "required": ["a", "b"],
            "additionalProperties": False,
        }

        # Call tools using override names
        result_1 = await workbench.call_tool("multiply_by_two", {"x": 5})
        assert result_1.name == "multiply_by_two"  # Should return the override name
        assert result_1.result[0].type == "TextResultContent"
        assert result_1.result[0].content == "10"
        assert result_1.to_text() == "10"
        assert result_1.is_error is False

        # Call tool using original name (should still work for description-only override)
        result_2 = await workbench.call_tool("add", {"a": 3, "b": 7})
        assert result_2.name == "add"
        assert result_2.result[0].type == "TextResultContent"
        assert result_2.result[0].content == "10"
        assert result_2.to_text() == "10"
        assert result_2.is_error is False

        # Test calling non-existent tool
        result_3 = await workbench.call_tool("nonexistent", {"x": 5})
        assert result_3.name == "nonexistent"
        assert result_3.is_error is True
        assert result_3.result[0].type == "TextResultContent"
        assert "Tool nonexistent not found" in result_3.result[0].content