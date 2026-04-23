def test_responses_api_logprobs_with_return_tokens_as_token_ids():
    """Test that return_tokens_as_token_ids works in Responses API logprobs."""
    from unittest.mock import MagicMock

    from vllm.entrypoints.openai.engine.serving import OpenAIServing
    from vllm.entrypoints.openai.responses.serving import OpenAIServingResponses
    from vllm.logprobs import Logprob as SampleLogprob

    serving = MagicMock(spec=OpenAIServingResponses)
    serving.return_tokens_as_token_ids = True
    serving._get_decoded_token = OpenAIServing._get_decoded_token

    tokenizer = MagicMock()
    tokenizer.decode = lambda token_id: "decoded"

    token_ids = [100, 200, 300]
    sample_logprobs = [
        {100: SampleLogprob(logprob=-0.5, decoded_token="hello")},
        {200: SampleLogprob(logprob=-1.2, decoded_token="world")},
        {300: SampleLogprob(logprob=-0.8, decoded_token="!")},
    ]

    result = OpenAIServingResponses._create_response_logprobs(
        serving,
        token_ids=token_ids,
        logprobs=sample_logprobs,
        tokenizer=tokenizer,
        top_logprobs=1,
    )

    assert len(result) == 3
    assert result[0].token == "token_id:100"
    assert result[1].token == "token_id:200"
    assert result[2].token == "token_id:300"
    assert result[0].logprob == -0.5
    assert result[1].logprob == -1.2
    assert result[2].logprob == -0.8