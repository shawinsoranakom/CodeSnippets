def _convert_to_message(message: MessageLikeRepresentation) -> BaseMessage:
    """Instantiate a `Message` from a variety of message formats.

    The message format can be one of the following:

    - `BaseMessagePromptTemplate`
    - `BaseMessage`
    - 2-tuple of (role string, template); e.g., (`'human'`, `'{user_input}'`)
    - dict: a message dict with role and content keys
    - string: shorthand for (`'human'`, template); e.g., `'{user_input}'`

    Args:
        message: a representation of a message in one of the supported formats.

    Returns:
        An instance of a message or a message template.

    Raises:
        NotImplementedError: if the message type is not supported.
        ValueError: if the message dict does not contain the required keys.

    """
    if isinstance(message, BaseMessage):
        message_ = message
    elif isinstance(message, Sequence):
        if isinstance(message, str):
            message_ = _create_message_from_message_type("human", message)
        else:
            try:
                message_type_str, template = message
            except ValueError as e:
                msg = "Message as a sequence must be (role string, template)"
                raise NotImplementedError(msg) from e
            message_ = _create_message_from_message_type(message_type_str, template)
    elif isinstance(message, dict):
        msg_kwargs = message.copy()
        try:
            try:
                msg_type = msg_kwargs.pop("role")
            except KeyError:
                msg_type = msg_kwargs.pop("type")
            # None msg content is not allowed
            msg_content = msg_kwargs.pop("content") or ""
        except KeyError as e:
            msg = f"Message dict must contain 'role' and 'content' keys, got {message}"
            msg = create_message(
                message=msg, error_code=ErrorCode.MESSAGE_COERCION_FAILURE
            )
            raise ValueError(msg) from e
        message_ = _create_message_from_message_type(
            msg_type, msg_content, **msg_kwargs
        )
    else:
        msg = f"Unsupported message type: {type(message)}"
        msg = create_message(message=msg, error_code=ErrorCode.MESSAGE_COERCION_FAILURE)
        raise NotImplementedError(msg)

    return message_