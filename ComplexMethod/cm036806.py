async def test_single_completion(client: openai.AsyncOpenAI, model_name: str):
    _cleanup()
    completion = await client.completions.create(
        model=model_name, prompt="Hello, my name is", max_tokens=5, temperature=0.0
    )

    assert completion.id is not None
    assert completion.choices is not None and len(completion.choices) == 1
    assert completion.model == MODEL_NAME
    assert len(completion.choices) == 1
    assert len(completion.choices[0].text) >= 5
    assert completion.choices[0].finish_reason == "length"
    assert completion.usage == openai.types.CompletionUsage(
        completion_tokens=5, prompt_tokens=6, total_tokens=11
    )