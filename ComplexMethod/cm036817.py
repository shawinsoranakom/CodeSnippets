async def test_echo_logprob_completion(
    client: openai.AsyncOpenAI, model_name: str, logprobs_arg: int
):
    tokenizer = get_tokenizer(tokenizer_name=MODEL_NAME)
    # test using text and token IDs
    for prompt in ("Hello, my name is", [0, 0, 0, 0, 0]):
        completion = await client.completions.create(
            model=model_name,
            prompt=prompt,
            max_tokens=5,
            temperature=0.0,
            echo=True,
            logprobs=logprobs_arg,
        )

        prompt_text = tokenizer.decode(prompt) if isinstance(prompt, list) else prompt
        assert re.search(r"^" + prompt_text, completion.choices[0].text)
        logprobs = completion.choices[0].logprobs
        assert logprobs is not None
        assert len(logprobs.text_offset) > 5
        assert len(logprobs.token_logprobs) > 5 and logprobs.token_logprobs[0] is None
        assert len(logprobs.top_logprobs) > 5 and logprobs.top_logprobs[0] is None
        for top_logprobs in logprobs.top_logprobs[1:]:
            assert max(logprobs_arg, 1) <= len(top_logprobs) <= logprobs_arg + 1
        assert len(logprobs.tokens) > 5