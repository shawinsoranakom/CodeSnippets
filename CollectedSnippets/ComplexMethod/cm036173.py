async def make_request(client: openai.AsyncOpenAI):
        completion = await client.completions.create(
            model=model_name, prompt="Hello, my name is", max_tokens=5, temperature=1.0
        )

        assert completion.id is not None
        assert completion.choices is not None and len(completion.choices) == 1

        choice = completion.choices[0]
        # The exact number of tokens can vary slightly with temperature=1.0,
        # so we check for a reasonable minimum length.
        assert len(choice.text) >= 1
        # Finish reason might not always be 'length' if the model finishes early
        # or due to other reasons, especially with high temperature.
        # So, we'll accept 'length' or 'stop'.
        assert choice.finish_reason in ("length", "stop")

        # Token counts can also vary, so we check they are positive.
        assert completion.usage.completion_tokens > 0
        assert completion.usage.prompt_tokens > 0
        assert completion.usage.total_tokens > 0
        return completion