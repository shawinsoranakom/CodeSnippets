async def test_openai_structured_output_with_streaming_tool_calls(
    model: str, openai_client: OpenAIChatCompletionClient
) -> None:
    class AgentResponse(BaseModel):
        thoughts: str
        response: Literal["happy", "sad", "neutral"]

    def sentiment_analysis(text: str) -> str:
        """Given a text, return the sentiment."""
        return "happy" if "happy" in text else "sad" if "sad" in text else "neutral"

    tool = FunctionTool(sentiment_analysis, description="Sentiment Analysis", strict=True)

    extra_create_args = {"tool_choice": "required"}

    chunks1: List[str | CreateResult] = []
    stream1 = openai_client.create_stream(
        messages=[
            SystemMessage(content="Analyze input text sentiment using the tool provided."),
            UserMessage(content="I am happy.", source="user"),
        ],
        tools=[tool],
        extra_create_args=extra_create_args,
        json_output=AgentResponse,
    )
    async for chunk in stream1:
        chunks1.append(chunk)
    assert len(chunks1) > 0
    create_result1 = chunks1[-1]
    assert isinstance(create_result1, CreateResult)
    assert isinstance(create_result1.content, list)
    assert len(create_result1.content) == 1
    assert isinstance(create_result1.content[0], FunctionCall)
    assert create_result1.content[0].name == "sentiment_analysis"
    assert json.loads(create_result1.content[0].arguments) == {"text": "I am happy."}
    assert create_result1.finish_reason == "function_calls"

    stream2 = openai_client.create_stream(
        messages=[
            SystemMessage(content="Analyze input text sentiment using the tool provided."),
            UserMessage(content="I am happy.", source="user"),
            AssistantMessage(content=create_result1.content, source="assistant"),
            FunctionExecutionResultMessage(
                content=[
                    FunctionExecutionResult(
                        content="happy", call_id=create_result1.content[0].id, is_error=False, name=tool.name
                    )
                ]
            ),
        ],
        json_output=AgentResponse,
    )
    chunks2: List[str | CreateResult] = []
    async for chunk in stream2:
        chunks2.append(chunk)
    assert len(chunks2) > 0
    create_result2 = chunks2[-1]
    assert isinstance(create_result2, CreateResult)
    assert isinstance(create_result2.content, str)
    parsed_response = AgentResponse.model_validate(json.loads(create_result2.content))
    assert parsed_response.thoughts
    assert parsed_response.response in ["happy", "sad", "neutral"]