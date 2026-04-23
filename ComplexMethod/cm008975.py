def test_max_tools_with_duplicates(self) -> None:
        """Test that max_tools works correctly with duplicate selections."""
        model_requests: list[ModelRequest] = []

        @wrap_model_call
        def trace_model_requests(
            request: ModelRequest, handler: Callable[[ModelRequest], ModelResponse]
        ) -> ModelResponse:
            model_requests.append(request)
            return handler(request)

        # Selector returns duplicates but max_tools=2
        tool_selection_model = FakeModel(
            messages=cycle(
                [
                    AIMessage(
                        content="",
                        tool_calls=[
                            {
                                "name": "ToolSelectionResponse",
                                "id": "1",
                                "args": {
                                    "tools": [
                                        "get_weather",
                                        "get_weather",
                                        "search_web",
                                        "search_web",
                                        "calculate",
                                    ]
                                },
                            }
                        ],
                    ),
                ]
            )
        )

        model = FakeModel(messages=iter([AIMessage(content="Done")]))

        tool_selector = LLMToolSelectorMiddleware(max_tools=2, model=tool_selection_model)

        agent = create_agent(
            model=model,
            tools=[get_weather, search_web, calculate],
            middleware=[tool_selector, trace_model_requests],
        )

        agent.invoke({"messages": [HumanMessage("test")]})

        # Should deduplicate and respect max_tools
        assert len(model_requests) > 0
        for request in model_requests:
            tool_names = []
            for tool_ in request.tools:
                assert isinstance(tool_, BaseTool)
                tool_names.append(tool_.name)
            assert len(tool_names) == 2
            assert "get_weather" in tool_names
            assert "search_web" in tool_names