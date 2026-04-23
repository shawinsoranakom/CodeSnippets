async def test_summarization_middleware_full_workflow_async() -> None:
    """Test SummarizationMiddleware complete summarization workflow."""

    class MockModel(BaseChatModel):
        @override
        def _generate(
            self,
            messages: list[BaseMessage],
            stop: list[str] | None = None,
            run_manager: CallbackManagerForLLMRun | None = None,
            **kwargs: Any,
        ) -> ChatResult:
            return ChatResult(generations=[ChatGeneration(message=AIMessage(content="Blep"))])

        @override
        async def _agenerate(
            self,
            messages: list[BaseMessage],
            stop: list[str] | None = None,
            run_manager: AsyncCallbackManagerForLLMRun | None = None,
            **kwargs: Any,
        ) -> ChatResult:
            return ChatResult(generations=[ChatGeneration(message=AIMessage(content="Blip"))])

        @property
        def _llm_type(self) -> str:
            return "mock"

    middleware = SummarizationMiddleware(
        model=MockModel(), trigger=("tokens", 1000), keep=("messages", 2)
    )

    # Mock high token count to trigger summarization
    def mock_token_counter(_: Iterable[MessageLikeRepresentation]) -> int:
        return 1500  # Above threshold

    middleware.token_counter = mock_token_counter

    messages: list[AnyMessage] = [
        HumanMessage(content="1"),
        HumanMessage(content="2"),
        HumanMessage(content="3"),
        HumanMessage(content="4"),
        HumanMessage(content="5"),
    ]

    state = AgentState[Any](messages=messages)
    result = await middleware.abefore_model(state, Runtime())

    assert result is not None
    assert "messages" in result
    assert len(result["messages"]) > 0

    expected_types = ["remove", "human", "human", "human"]
    actual_types = [message.type for message in result["messages"]]
    assert actual_types == expected_types
    assert [message.content for message in result["messages"][2:]] == ["4", "5"]

    summary_message = result["messages"][1]
    assert "Blip" in summary_message.text