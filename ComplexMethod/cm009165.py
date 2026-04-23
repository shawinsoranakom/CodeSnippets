def test_structured_output_strict(
    model: str,
    method: Literal["function_calling", "json_schema"],
    use_responses_api: bool,
) -> None:
    """Test to verify structured output with strict=True."""

    from pydantic import BaseModel as BaseModelProper
    from pydantic import Field as FieldProper

    llm = ChatOpenAI(model=model, use_responses_api=use_responses_api)

    class Joke(BaseModelProper):
        """Joke to tell user."""

        setup: str = FieldProper(description="question to set up a joke")
        punchline: str = FieldProper(description="answer to resolve the joke")

    # Pydantic class
    chat = llm.with_structured_output(Joke, method=method, strict=True)
    result = chat.invoke("Tell me a joke about cats.")
    assert isinstance(result, Joke)

    for chunk in chat.stream("Tell me a joke about cats."):
        assert isinstance(chunk, Joke)

    # Schema
    chat = llm.with_structured_output(
        Joke.model_json_schema(), method=method, strict=True
    )
    result = chat.invoke("Tell me a joke about cats.")
    assert isinstance(result, dict)
    assert set(result.keys()) == {"setup", "punchline"}

    for chunk in chat.stream("Tell me a joke about cats."):
        assert isinstance(chunk, dict)
    assert isinstance(chunk, dict)  # for mypy
    assert set(chunk.keys()) == {"setup", "punchline"}