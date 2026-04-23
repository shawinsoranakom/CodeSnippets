def test_combine_llm_outputs_with_token_details() -> None:
    """Test that _combine_llm_outputs properly combines nested token details."""
    llm = ChatGroq(model="test-model")

    llm_outputs: list[dict[str, Any] | None] = [
        {
            "token_usage": {
                "prompt_tokens": 100,
                "completion_tokens": 50,
                "total_tokens": 150,
                "input_tokens_details": {"cached_tokens": 80},
                "output_tokens_details": {"reasoning_tokens": 20},
            },
            "model_name": "test-model",
            "system_fingerprint": "fp_123",
        },
        {
            "token_usage": {
                "prompt_tokens": 200,
                "completion_tokens": 100,
                "total_tokens": 300,
                "input_tokens_details": {"cached_tokens": 150},
                "output_tokens_details": {"reasoning_tokens": 40},
            },
            "model_name": "test-model",
            "system_fingerprint": "fp_123",
        },
    ]

    result = llm._combine_llm_outputs(llm_outputs)

    assert result["token_usage"]["prompt_tokens"] == 300
    assert result["token_usage"]["completion_tokens"] == 150
    assert result["token_usage"]["total_tokens"] == 450
    assert result["token_usage"]["input_tokens_details"]["cached_tokens"] == 230
    assert result["token_usage"]["output_tokens_details"]["reasoning_tokens"] == 60
    assert result["model_name"] == "test-model"
    assert result["system_fingerprint"] == "fp_123"