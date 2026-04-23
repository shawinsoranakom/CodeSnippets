async def test_parallel_no_streaming(client: openai.AsyncOpenAI, model_name: str):
    """Parallel sampling without streaming.
    A single request output contains a list of completions.
    """

    prompt = "What is an LLM?"
    n = 3
    max_tokens = 50  # we want some to finish earlier than others

    # High temperature to maximize chance of unique completions.
    completion = await client.completions.create(
        model=model_name,
        prompt=prompt,
        max_tokens=max_tokens,
        n=n,
        temperature=1.0,
        stream=False,
        logprobs=0,
        seed=42,
    )

    # Assert `n` completions
    num_completions = len(completion.choices)
    assert num_completions == n, f"Num completions {num_completions} but expected {n}."
    completion_repeats: dict[str, int] = {}
    output_token_lengths = set()
    for idx, choice in enumerate(completion.choices):
        # Assert correct completion index & some finish reason.
        assert choice.index == idx, f"Index {choice.index} but expected {idx}."
        assert choice.finish_reason is not None, "None finish_reason is invalid."
        text = choice.text
        completion_repeats[text] = completion_repeats.get(text, 0) + 1
        output_token_lengths.add(len(choice.logprobs.tokens))
    # Assert subrequests finished at different times
    assert len(output_token_lengths) > 1
    # Assert `n` unique completions
    num_unique = len(completion_repeats)
    if num_unique != n:
        repeats = {txt: num for (txt, num) in completion_repeats.items() if num > 1}
        raise AssertionError(
            f"Expected {n} unique completions, got {num_unique}; repeats: {repeats}."
        )