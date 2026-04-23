def _last_max_tokens(
    messages: Sequence[BaseMessage],
    *,
    max_tokens: int,
    token_counter: Callable[[list[BaseMessage]], int],
    text_splitter: Callable[[str], list[str]],
    allow_partial: bool = False,
    include_system: bool = False,
    start_on: str | type[BaseMessage] | Sequence[str | type[BaseMessage]] | None = None,
    end_on: str | type[BaseMessage] | Sequence[str | type[BaseMessage]] | None = None,
) -> list[BaseMessage]:
    messages = list(messages)
    if len(messages) == 0:
        return []

    # Filter out messages after end_on type
    if end_on:
        for _ in range(len(messages)):
            if not _is_message_type(messages[-1], end_on):
                messages.pop()
            else:
                break

    # Handle system message preservation
    system_message = None
    if include_system and len(messages) > 0 and isinstance(messages[0], SystemMessage):
        system_message = messages[0]
        messages = messages[1:]

    # Reverse messages to use _first_max_tokens with reversed logic
    reversed_messages = messages[::-1]

    # Calculate remaining tokens after accounting for system message if present
    remaining_tokens = max_tokens
    if system_message:
        system_tokens = token_counter([system_message])
        remaining_tokens = max(0, max_tokens - system_tokens)

    reversed_result = _first_max_tokens(
        reversed_messages,
        max_tokens=remaining_tokens,
        token_counter=token_counter,
        text_splitter=text_splitter,
        partial_strategy="last" if allow_partial else None,
        end_on=start_on,
    )

    # Re-reverse the messages and add back the system message if needed
    result = reversed_result[::-1]
    if system_message:
        result = [system_message, *result]

    return result