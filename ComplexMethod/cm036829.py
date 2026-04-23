async def test_chat_streaming_image(
    client: openai.AsyncOpenAI, model_name: str, image_url: str
):
    messages = dummy_messages_from_image_url(image_url)

    # test single completion
    chat_completion = await client.chat.completions.create(
        model=model_name,
        messages=messages,
        max_completion_tokens=10,
        temperature=0.0,
    )
    output = chat_completion.choices[0].message.content
    stop_reason = chat_completion.choices[0].finish_reason

    # test streaming
    stream = await client.chat.completions.create(
        model=model_name,
        messages=messages,
        max_completion_tokens=10,
        temperature=0.0,
        stream=True,
    )
    chunks: list[str] = []
    finish_reason_count = 0
    async for chunk in stream:
        delta = chunk.choices[0].delta
        if delta.role:
            assert delta.role == "assistant", (
                f"Expected role='assistant' in stream delta, got {delta.role!r}"
            )
        if delta.content:
            chunks.append(delta.content)
        if chunk.choices[0].finish_reason is not None:
            finish_reason_count += 1
    # finish reason should only return in last block
    assert finish_reason_count == 1, (
        f"Expected exactly 1 finish_reason across stream chunks, "
        f"got {finish_reason_count}"
    )
    assert chunk.choices[0].finish_reason == stop_reason, (
        f"Stream finish_reason={chunk.choices[0].finish_reason!r} "
        f"doesn't match non-stream finish_reason={stop_reason!r}"
    )

    streamed_text = "".join(chunks)
    assert streamed_text == output, (
        f"Streamed output doesn't match non-streamed for {image_url}.\n"
        f"  streamed:     {streamed_text!r}\n"
        f"  non-streamed: {output!r}"
    )