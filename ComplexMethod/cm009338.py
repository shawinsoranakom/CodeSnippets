async def test_agenerate() -> None:
    """Test async generation."""
    n = 1
    chat = ChatGroq(model=DEFAULT_MODEL_NAME, max_tokens=10, n=1)
    message = HumanMessage(content="Hello")
    response = await chat.agenerate([[message], [message]])
    assert isinstance(response, LLMResult)
    assert len(response.generations) == 2
    assert response.llm_output
    assert response.llm_output["model_name"] == chat.model_name
    for generations in response.generations:
        assert len(generations) == n
        for generation in generations:
            assert isinstance(generation, ChatGeneration)
            assert isinstance(generation.text, str)
            assert generation.text == generation.message.content