def test_always_include_tools_present(self) -> None:
        """Test that always_include tools are always present in the request."""
        model_requests = []

        @wrap_model_call
        def trace_model_requests(
            request: ModelRequest, handler: Callable[[ModelRequest], ModelResponse]
        ) -> ModelResponse:
            model_requests.append(request)
            return handler(request)

        # Selector picks only search_web
        tool_selection_model = FakeModel(
            messages=cycle(
                [
                    AIMessage(
                        content="",
                        tool_calls=[
                            {
                                "name": "ToolSelectionResponse",
                                "id": "1",
                                "args": {"tools": ["search_web"]},
                            }
                        ],
                    ),
                ]
            )
        )

        model = FakeModel(messages=iter([AIMessage(content="Done")]))

        # But send_email is always included
        tool_selector = LLMToolSelectorMiddleware(
            max_tools=1, always_include=["send_email"], model=tool_selection_model
        )

        agent = create_agent(
            model=model,
            tools=[get_weather, search_web, send_email],
            middleware=[tool_selector, trace_model_requests],
        )

        agent.invoke({"messages": [HumanMessage("test")]})

        # Both selected and always_include tools should be present
        assert len(model_requests) > 0
        for request in model_requests:
            tool_names = []
            for tool_ in request.tools:
                assert isinstance(tool_, BaseTool)
                tool_names.append(tool_.name)
            assert "search_web" in tool_names
            assert "send_email" in tool_names
            assert len(tool_names) == 2