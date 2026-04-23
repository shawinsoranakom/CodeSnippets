async def test_single_chat_session(client: openai.AsyncOpenAI, model_name: str):
    messages = [
        {"role": "system", "content": "you are a helpful assistant"},
        {"role": "user", "content": "what is 1+1?"},
    ]
    # test single completion
    chat_completion = await client.chat.completions.create(
        model=model_name,
        messages=messages,
        max_completion_tokens=5,
        logprobs=True,
        top_logprobs=5,
    )
    assert chat_completion.id is not None
    assert len(chat_completion.choices) == 1

    choice = chat_completion.choices[0]

    assert choice.finish_reason == "length"
    assert chat_completion.usage == openai.types.CompletionUsage(
        completion_tokens=5, prompt_tokens=37, total_tokens=42
    )

    message = choice.message
    assert message.content is not None and len(message.content) >= 5
    assert message.role == "assistant"
    messages.append({"role": "assistant", "content": message.content})

    # test multi-turn dialogue
    messages.append({"role": "user", "content": "express your result in json"})
    chat_completion = await client.chat.completions.create(
        model=model_name,
        messages=messages,
        max_completion_tokens=5,
    )
    message = chat_completion.choices[0].message
    assert message.content is not None and len(message.content) >= 0