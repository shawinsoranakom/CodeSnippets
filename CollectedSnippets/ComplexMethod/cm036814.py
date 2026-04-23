async def test_parallel_streaming(client: openai.AsyncOpenAI, model_name: str):
    """Streaming for parallel sampling.
    The tokens from multiple samples, are flattened into a single stream,
    with an index to indicate which sample the token belongs to.
    """

    prompt = "What is an LLM?"
    n = 3
    max_tokens = 50  # we want some to finish earlier than others

    stream = await client.completions.create(
        model=model_name,
        prompt=prompt,
        max_tokens=max_tokens,
        n=n,
        temperature=1.0,
        stream=True,
        seed=42,
    )
    chunks: list[list[str]] = [[] for _ in range(n)]
    finish_reason_count = 0
    async for chunk in stream:
        index = chunk.choices[0].index
        text = chunk.choices[0].text
        chunks[index].append(text)
        if chunk.choices[0].finish_reason is not None:
            finish_reason_count += 1
    # Assert `n` completions with correct finish reasons
    assert finish_reason_count == n, (
        f"Expected {n} completions with valid indices and finish_reason."
    )
    completion_repeats: dict[str, int] = {}
    chunk_lengths = set()
    for chunk in chunks:
        chunk_len = len(chunk)
        # Assert correct number of completion tokens
        chunk_lengths.add(chunk_len)
        assert chunk_len <= max_tokens, (
            f"max_tokens={max_tokens} but chunk len is {chunk_len}."
        )
        text = "".join(chunk)
        completion_repeats[text] = completion_repeats.get(text, 0) + 1
        print(text)
    # Assert subrequests finished at different times
    assert len(chunk_lengths) > 1
    # Assert `n` unique completions
    num_unique = len(completion_repeats)
    if num_unique != n:
        repeats = {txt: num for (txt, num) in completion_repeats.items() if num > 1}
        raise AssertionError(
            f"{num_unique} unique completions, expected {n}; repeats: {repeats}"
        )