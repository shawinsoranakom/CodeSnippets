def construct_harmony_previous_input_messages(
    request: ResponsesRequest,
) -> list[Message]:
    """Build a Harmony message list from request.previous_input_messages.

    Filters out system/developer messages to match OpenAI behavior where
    instructions are always taken from the most recent Responses API request.
    """
    messages: list[Message] = []
    if request.previous_input_messages:
        for message in request.previous_input_messages:
            # Handle both Message objects and dictionary inputs
            if isinstance(message, Message):
                message_role = message.author.role
                if message_role == Role.SYSTEM or message_role == Role.DEVELOPER:
                    continue
                messages.append(message)
            else:
                harmony_messages = response_previous_input_to_harmony(message)
                for harmony_msg in harmony_messages:
                    message_role = harmony_msg.author.role
                    if message_role == Role.SYSTEM or message_role == Role.DEVELOPER:
                        continue
                    messages.append(harmony_msg)
    return messages