async def test_agenerate_streaming() -> None:
    """Test that streaming correctly invokes on_llm_new_token callback."""
    callback_handler = FakeCallbackHandlerWithChatStart()
    chat = ChatGroq(
        model=DEFAULT_MODEL_NAME,
        max_tokens=10,
        streaming=True,
        temperature=0,
        callbacks=[callback_handler],
    )
    message = HumanMessage(content="Welcome to the Groqetship")
    response = await chat.agenerate([[message], [message]])
    assert callback_handler.llm_streams > 0
    assert isinstance(response, LLMResult)
    assert len(response.generations) == 2
    assert response.llm_output is not None
    assert response.llm_output["model_name"] == chat.model_name
    for generations in response.generations:
        assert len(generations) == 1
        for generation in generations:
            assert isinstance(generation, ChatGeneration)
            assert isinstance(generation.text, str)
            assert generation.text == generation.message.content