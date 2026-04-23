def test_always_include_not_counted_against_max(self) -> None:
        """Test that always_include tools don't count against max_tools limit."""
        model_requests = []

        @wrap_model_call
        def trace_model_requests(
            request: ModelRequest, handler: Callable[[ModelRequest], ModelResponse]
        ) -> ModelResponse:
            model_requests.append(request)
            return handler(request)

        # Selector picks 2 tools
        tool_selection_model = FakeModel(
            messages=cycle(
                [
                    AIMessage(
                        content="",
                        tool_calls=[
                            {
                                "name": "ToolSelectionResponse",
                                "id": "1",
                                "args": {"tools": ["get_weather", "search_web"]},
                            }
                        ],
                    ),
                ]
            )
        )

        model = FakeModel(messages=iter([AIMessage(content="Done")]))

        # max_tools=2, but we also have 2 always_include tools
        tool_selector = LLMToolSelectorMiddleware(
            max_tools=2,
            always_include=["send_email", "calculate"],
            model=tool_selection_model,
        )

        agent = create_agent(
            model=model,
            tools=[get_weather, search_web, calculate, send_email],
            middleware=[tool_selector, trace_model_requests],
        )

        agent.invoke({"messages": [HumanMessage("test")]})

        # Should have 2 selected + 2 always_include = 4 total
        assert len(model_requests) > 0
        for request in model_requests:
            assert len(request.tools) == 4
            tool_names = []
            for tool_ in request.tools:
                assert isinstance(tool_, BaseTool)
                tool_names.append(tool_.name)
            assert "get_weather" in tool_names
            assert "search_web" in tool_names
            assert "send_email" in tool_names
            assert "calculate" in tool_names