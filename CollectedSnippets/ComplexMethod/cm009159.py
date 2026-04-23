def test_openai_invoke() -> None:
    """Test invoke tokens from ChatOpenAI."""
    llm = ChatOpenAI(
        model="gpt-5-nano",
        service_tier="flex",  # Also test service_tier
        max_retries=3,  # Add retries for 503 capacity errors
    )

    result = llm.invoke("Hello", config={"tags": ["foo"]})
    assert isinstance(result.content, str)

    usage_metadata = result.usage_metadata  # type: ignore[attr-defined]

    # assert no response headers if include_response_headers is not set
    assert "headers" not in result.response_metadata
    assert usage_metadata is not None
    flex_input = usage_metadata.get("input_token_details", {}).get("flex")
    assert isinstance(flex_input, int)
    assert flex_input > 0
    assert flex_input == usage_metadata.get("input_tokens")
    flex_output = usage_metadata.get("output_token_details", {}).get("flex")
    assert isinstance(flex_output, int)
    assert flex_output > 0
    # GPT-5-nano/reasoning model specific. Remove if model used in test changes.
    flex_reasoning = usage_metadata.get("output_token_details", {}).get(
        "flex_reasoning"
    )
    assert isinstance(flex_reasoning, int)
    assert flex_reasoning > 0
    assert flex_reasoning + flex_output == usage_metadata.get("output_tokens")