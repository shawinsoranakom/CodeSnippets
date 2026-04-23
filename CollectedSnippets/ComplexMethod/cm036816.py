async def test_batch_completions(client: openai.AsyncOpenAI, model_name: str):
    # test both text and token IDs
    for prompts in (["Hello, my name is"] * 2, [[0, 0, 0, 0, 0]] * 2):
        # test simple list
        batch = await client.completions.create(
            model=model_name,
            prompt=prompts,
            max_tokens=5,
            temperature=0.0,
        )
        assert len(batch.choices) == 2
        assert batch.choices[0].text == batch.choices[1].text

        # test n = 2
        batch = await client.completions.create(
            model=model_name,
            prompt=prompts,
            n=2,
            max_tokens=5,
            temperature=0.0,
            extra_body=dict(
                # NOTE: this has to be true for n > 1 in vLLM, but
                # not necessary for official client.
                use_beam_search=True
            ),
        )
        assert len(batch.choices) == 4
        assert batch.choices[0].text != batch.choices[1].text, (
            "beam search should be different"
        )
        assert batch.choices[0].text == batch.choices[2].text, (
            "two copies of the same prompt should be the same"
        )
        assert batch.choices[1].text == batch.choices[3].text, (
            "two copies of the same prompt should be the same"
        )

        # test streaming
        batch = await client.completions.create(
            model=model_name,
            prompt=prompts,
            max_tokens=5,
            temperature=0.0,
            stream=True,
        )
        texts = [""] * 2
        async for chunk in batch:
            assert len(chunk.choices) == 1
            choice = chunk.choices[0]
            texts[choice.index] += choice.text
        assert texts[0] == texts[1]