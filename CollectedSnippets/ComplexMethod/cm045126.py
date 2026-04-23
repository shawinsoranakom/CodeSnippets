async def test_openai_structured_output_with_tool_calls(model: str, openai_client: OpenAIChatCompletionClient) -> None:
    class AgentResponse(BaseModel):
        thoughts: str
        response: Literal["happy", "sad", "neutral"]

    def sentiment_analysis(text: str) -> str:
        """Given a text, return the sentiment."""
        return "happy" if "happy" in text else "sad" if "sad" in text else "neutral"

    tool = FunctionTool(sentiment_analysis, description="Sentiment Analysis", strict=True)

    extra_create_args = {"tool_choice": "required"}

    response1 = await openai_client.create(
        messages=[
            SystemMessage(content="Analyze input text sentiment using the tool provided."),
            UserMessage(content="I am happy.", source="user"),
        ],
        tools=[tool],
        extra_create_args=extra_create_args,
        json_output=AgentResponse,
    )
    assert isinstance(response1.content, list)
    assert len(response1.content) == 1
    assert isinstance(response1.content[0], FunctionCall)
    assert response1.content[0].name == "sentiment_analysis"
    assert json.loads(response1.content[0].arguments) == {"text": "I am happy."}
    assert response1.finish_reason == "function_calls"

    response2 = await openai_client.create(
        messages=[
            SystemMessage(content="Analyze input text sentiment using the tool provided."),
            UserMessage(content="I am happy.", source="user"),
            AssistantMessage(content=response1.content, source="assistant"),
            FunctionExecutionResultMessage(
                content=[
                    FunctionExecutionResult(
                        content="happy", call_id=response1.content[0].id, is_error=False, name=tool.name
                    )
                ]
            ),
        ],
        json_output=AgentResponse,
    )
    assert isinstance(response2.content, str)
    parsed_response = AgentResponse.model_validate(json.loads(response2.content))
    assert parsed_response.thoughts
    assert parsed_response.response in ["happy", "sad", "neutral"]