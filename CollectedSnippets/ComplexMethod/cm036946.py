async def test_single_completion(client: openai.AsyncOpenAI):
    completion = await client.completions.create(
        model=MODEL_NAME,
        prompt="Hello, my name is",
        max_tokens=5,
        extra_headers={"endpoint-load-metrics-format": "JSON"},
        temperature=0.0,
    )

    assert completion.id is not None
    assert completion.choices is not None and len(completion.choices) == 1

    choice = completion.choices[0]
    assert len(choice.text) >= 5
    assert choice.finish_reason == "length"
    # When using Qwen3-0.6B, prompt tokens=[9707, 11, 847, 829, 374]
    assert completion.usage == openai.types.CompletionUsage(
        completion_tokens=5, prompt_tokens=5, total_tokens=10
    )

    # test using token IDs
    completion = await client.completions.create(
        model=MODEL_NAME,
        prompt=[0, 0, 0, 0, 0],
        max_tokens=5,
        temperature=0.0,
    )
    assert len(completion.choices[0].text) >= 1
    assert completion.choices[0].prompt_logprobs is None