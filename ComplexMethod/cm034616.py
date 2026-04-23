async def stream_response(
    client: AsyncClient,
    input_text,
    conversation: ConversationManager,
    output_file: Optional[Path] = None,
    instructions: Optional[str] = None
) -> None:
    media = None
    if isinstance(input_text, tuple):
        media, input_text = input_text

    if instructions:
        conversation.add_message("system", instructions)

    conversation.add_message("user", input_text)

    create_args = {
        "model": conversation.model,
        "messages": conversation.get_messages(),
        "stream": True,
        "media": media,
        "conversation": conversation.conversation,
    }

    response_tokens = []
    last_chunk = None
    async for chunk in client.chat.completions.create(**create_args):
        last_chunk = chunk
        delta = chunk.choices[0].delta.content
        if not delta:
            continue
        if is_content(delta):
            response_tokens.append(delta)
        try:
            print(delta, end="", flush=True)
        except UnicodeEncodeError as e:
            debug.error(e)
            pass
    print()

    if last_chunk and hasattr(last_chunk, "conversation"):
        conversation.conversation = last_chunk.conversation

    media_chunk = next((t for t in response_tokens if isinstance(t, MediaResponse)), None)
    text_response = ""
    if media_chunk:
        text_response = response_tokens[0] if len(response_tokens) == 1 else "".join(str(t) for t in response_tokens)
    else:
        text_response = "".join(str(t) for t in response_tokens)

    if output_file:
        if save_content(text_response, media_chunk, str(output_file)):
            print(f"\n→ Response saved to '{output_file}'")

    if text_response:
        if not media_chunk:
            conversation.add_message("assistant", text_response)
    else:
        raise RuntimeError("No response received")