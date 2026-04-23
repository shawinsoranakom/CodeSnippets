def test_tool_runtime_config_access() -> None:
    """Test tools can access config through ToolRuntime."""
    config_data: dict[str, Any] = {}

    @tool
    def config_tool(x: int, runtime: ToolRuntime) -> str:
        """Tool that accesses config."""
        config_data["config_exists"] = runtime.config is not None
        config_data["has_configurable"] = (
            "configurable" in runtime.config if runtime.config else False
        )
        if runtime.config:
            config_data["config_keys"] = list(runtime.config.keys())
            config_data["recursion_limit"] = runtime.config.get("recursion_limit")
            config_data["metadata"] = runtime.config.get("metadata")
        return f"Config accessed for {x}"

    agent = create_agent(
        model=FakeToolCallingModel(
            tool_calls=[
                [{"args": {"x": 5}, "id": "config_call", "name": "config_tool"}],
                [],
            ]
        ),
        tools=[config_tool],
        system_prompt="You are a helpful assistant.",
    )

    result = agent.invoke(
        {"messages": [HumanMessage("Test config")]},
    )

    assert config_data["config_exists"] is True
    assert "config_keys" in config_data
    assert config_data["recursion_limit"] == 9999
    assert config_data["metadata"]["ls_integration"] == "langchain_create_agent"

    tool_message = result["messages"][2]
    assert isinstance(tool_message, ToolMessage)
    assert tool_message.content == "Config accessed for 5"

    result = agent.invoke(
        {"messages": [HumanMessage("Test config again")]},
        config={"recursion_limit": 7},
    )

    assert config_data["recursion_limit"] == 7

    tool_message = result["messages"][2]
    assert isinstance(tool_message, ToolMessage)
    assert tool_message.content == "Config accessed for 5"