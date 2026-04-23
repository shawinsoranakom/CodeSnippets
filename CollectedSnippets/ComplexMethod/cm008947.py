async def test_combined_injected_state_runtime_store_async() -> None:
    """Test that all injection mechanisms work together in async execution.

    This async version verifies that injected state, tool runtime, and injected
    store all work correctly with async tools in create_agent.
    """
    # Track what was injected
    injected_data = {}

    # Custom state schema
    class CustomState(AgentState[Any]):
        api_key: str
        request_id: str

    # Define explicit args schema that only includes LLM-controlled parameters
    # Note: state, runtime, and store are NOT in this schema
    search_schema = {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "The search query"},
            "max_results": {"type": "integer", "description": "Maximum number of results"},
        },
        "required": ["query", "max_results"],
    }

    @tool(args_schema=search_schema)
    async def async_multi_injection_tool(
        query: str,
        max_results: int,
        state: Annotated[Any, InjectedState],
        runtime: ToolRuntime,
        store: Annotated[Any, InjectedStore()],
    ) -> str:
        """Async tool with multiple injection types.

        Args:
            query: The search query (LLM-controlled).
            max_results: Maximum number of results (LLM-controlled).
            state: The graph state (injected).
            runtime: The tool runtime context (injected).
            store: The persistent store (injected).
        """
        # Capture all injected parameters
        injected_data["state"] = state
        injected_data["api_key"] = state.get("api_key", "unknown")
        injected_data["request_id"] = state.get("request_id", "unknown")
        injected_data["runtime"] = runtime
        injected_data["tool_call_id"] = runtime.tool_call_id
        injected_data["config"] = runtime.config
        injected_data["store"] = store

        # Verify we can write to the store
        if store is not None:
            await store.aput(("test", "namespace"), "test_key", {"query": query})
            # Read back to verify it worked
            item = await store.aget(("test", "namespace"), "test_key")
            injected_data["store_write_success"] = item is not None

        return f"Found {max_results} results for '{query}'"

    # Create model that calls the async tool
    model = FakeToolCallingModel(
        tool_calls=[
            [
                {
                    "name": "async_multi_injection_tool",
                    "args": {"query": "test search", "max_results": 10},
                    "id": "call_search_456",
                }
            ],
            [],
        ]
    )

    # Create agent with custom state and store
    agent = create_agent(
        model=model,
        tools=[async_multi_injection_tool],
        state_schema=CustomState,
        store=InMemoryStore(),
    )

    # Verify the tool's args schema only includes LLM-controlled parameters
    tool_args_schema = async_multi_injection_tool.args_schema
    assert isinstance(tool_args_schema, dict)
    assert "query" in tool_args_schema["properties"]
    assert "max_results" in tool_args_schema["properties"]
    assert "state" not in tool_args_schema["properties"]
    assert "runtime" not in tool_args_schema["properties"]
    assert "store" not in tool_args_schema["properties"]

    # Invoke async
    result = await agent.ainvoke(
        {
            "messages": [HumanMessage("Search for something")],
            "api_key": "sk-test-key-xyz",
            "request_id": "req_999",
        }
    )

    # Verify tool executed successfully
    tool_messages = [msg for msg in result["messages"] if isinstance(msg, ToolMessage)]
    assert len(tool_messages) == 1
    tool_message = tool_messages[0]
    assert tool_message.content == "Found 10 results for 'test search'"
    assert tool_message.tool_call_id == "call_search_456"

    # Verify all injections worked correctly
    assert injected_data["state"] is not None
    assert injected_data["api_key"] == "sk-test-key-xyz"
    assert injected_data["request_id"] == "req_999"

    # Verify runtime was injected
    assert injected_data["runtime"] is not None
    assert injected_data["tool_call_id"] == "call_search_456"
    assert injected_data["config"] is not None

    # Verify store was injected and writable
    assert injected_data["store"] is not None
    assert injected_data["store_write_success"] is True