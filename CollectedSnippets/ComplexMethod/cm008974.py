def test_multiple_always_include_tools(self) -> None:
        """Test that multiple always_include tools are all present."""
        model_requests = []

        @wrap_model_call
        def trace_model_requests(
            request: ModelRequest, handler: Callable[[ModelRequest], ModelResponse]
        ) -> ModelResponse:
            model_requests.append(request)
            return handler(request)

        # Selector picks 1 tool
        tool_selection_model = FakeModel(
            messages=cycle(
                [
                    AIMessage(
                        content="",
                        tool_calls=[
                            {
                                "name": "ToolSelectionResponse",
                                "id": "1",
                                "args": {"tools": ["get_weather"]},
                            }
                        ],
                    ),
                ]
            )
        )

        model = FakeModel(messages=iter([AIMessage(content="Done")]))

        tool_selector = LLMToolSelectorMiddleware(
            max_tools=1,
            always_include=["send_email", "calculate", "get_stock_price"],
            model=tool_selection_model,
        )

        agent = create_agent(
            model=model,
            tools=[get_weather, search_web, send_email, calculate, get_stock_price],
            middleware=[tool_selector, trace_model_requests],
        )

        agent.invoke({"messages": [HumanMessage("test")]})

        # Should have 1 selected + 3 always_include = 4 total
        assert len(model_requests) > 0
        for request in model_requests:
            assert len(request.tools) == 4
            tool_names = []
            for tool_ in request.tools:
                assert isinstance(tool_, BaseTool)
                tool_names.append(tool_.name)
            assert "get_weather" in tool_names
            assert "send_email" in tool_names
            assert "calculate" in tool_names
            assert "get_stock_price" in tool_names