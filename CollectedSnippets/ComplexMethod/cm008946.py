def test_combined_injected_state_runtime_store() -> None:
    """Test that all injection mechanisms work together in create_agent.

    This test verifies that a tool can receive injected state, tool runtime,
    and injected store simultaneously when specified in the function signature
    but not in the explicit args schema. This is modeled after the pattern
    from mre.py where multiple injection types are combined.
    """
    # Track what was injected
    injected_data = {}

    # Custom state schema with additional fields
    class CustomState(AgentState[Any]):
        user_id: str
        session_id: str

    # Define explicit args schema that only includes LLM-controlled parameters
    weather_schema = {
        "type": "object",
        "properties": {
            "location": {"type": "string", "description": "The location to get weather for"},
        },
        "required": ["location"],
    }

    @tool(args_schema=weather_schema)
    def multi_injection_tool(
        location: str,
        state: Annotated[Any, InjectedState],
        runtime: ToolRuntime,
        store: Annotated[Any, InjectedStore()],
    ) -> str:
        """Tool that uses injected state, runtime, and store together.

        Args:
            location: The location to get weather for (LLM-controlled).
            state: The graph state (injected).
            runtime: The tool runtime context (injected).
            store: The persistent store (injected).
        """
        # Capture all injected parameters
        injected_data["state"] = state
        injected_data["user_id"] = state.get("user_id", "unknown")
        injected_data["session_id"] = state.get("session_id", "unknown")
        injected_data["runtime"] = runtime
        injected_data["tool_call_id"] = runtime.tool_call_id
        injected_data["store"] = store
        injected_data["store_is_none"] = store is None

        # Verify runtime.state matches the state parameter
        injected_data["runtime_state_matches"] = runtime.state == state

        return f"Weather info for {location}"

    # Create model that calls the tool
    model = FakeToolCallingModel(
        tool_calls=[
            [
                {
                    "name": "multi_injection_tool",
                    "args": {"location": "San Francisco"},  # Only LLM-controlled arg
                    "id": "call_weather_123",
                }
            ],
            [],  # End the loop
        ]
    )

    # Create agent with custom state and store
    agent = create_agent(
        model=model,
        tools=[multi_injection_tool],
        state_schema=CustomState,
        store=InMemoryStore(),
    )

    # Verify the tool's args schema only includes LLM-controlled parameters
    tool_args_schema = multi_injection_tool.args_schema
    assert isinstance(tool_args_schema, dict)
    assert "location" in tool_args_schema["properties"]
    assert "state" not in tool_args_schema["properties"]
    assert "runtime" not in tool_args_schema["properties"]
    assert "store" not in tool_args_schema["properties"]

    # Invoke with custom state fields
    result = agent.invoke(
        {
            "messages": [HumanMessage("What's the weather like?")],
            "user_id": "user_42",
            "session_id": "session_abc123",
        }
    )

    # Verify tool executed successfully
    tool_messages = [msg for msg in result["messages"] if isinstance(msg, ToolMessage)]
    assert len(tool_messages) == 1
    tool_message = tool_messages[0]
    assert tool_message.content == "Weather info for San Francisco"
    assert tool_message.tool_call_id == "call_weather_123"

    # Verify all injections worked correctly
    assert injected_data["state"] is not None
    assert "messages" in injected_data["state"]

    # Verify custom state fields were accessible
    assert injected_data["user_id"] == "user_42"
    assert injected_data["session_id"] == "session_abc123"

    # Verify runtime was injected
    assert injected_data["runtime"] is not None
    assert injected_data["tool_call_id"] == "call_weather_123"

    # Verify store was injected
    assert injected_data["store_is_none"] is False
    assert injected_data["store"] is not None

    # Verify runtime.state matches the injected state
    assert injected_data["runtime_state_matches"] is True