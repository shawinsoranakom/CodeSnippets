def _convert_to_message_template(
    message: MessageLikeRepresentation,
    template_format: PromptTemplateFormat = "f-string",
) -> BaseMessage | BaseMessagePromptTemplate | BaseChatPromptTemplate:
    """Instantiate a message from a variety of message formats.

    A message can be represented using the following formats:

    1. `BaseMessagePromptTemplate`
    2. `BaseMessage`
    3. 2-tuple of `(message type, template)`; e.g., `('human', '{user_input}')`
    4. 2-tuple of `(message class, template)`
    5. A string which is shorthand for `('human', template)`; e.g., `'{user_input}'`

    Args:
        message: A representation of a message in one of the supported formats.
        template_format: Format of the template.

    Returns:
        An instance of a message or a message template.

    Raises:
        ValueError: If unexpected message type.
        ValueError: If 2-tuple does not have 2 elements.
    """
    if isinstance(message, (BaseMessagePromptTemplate, BaseChatPromptTemplate)):
        message_: BaseMessage | BaseMessagePromptTemplate | BaseChatPromptTemplate = (
            message
        )
    elif isinstance(message, BaseMessage):
        message_ = message
    elif isinstance(message, str):
        message_ = _create_template_from_message_type(
            "human", message, template_format=template_format
        )
    elif isinstance(message, (tuple, dict)):
        if isinstance(message, dict):
            if set(message.keys()) != {"content", "role"}:
                msg = (
                    "Expected dict to have exact keys 'role' and 'content'."
                    f" Got: {message}"
                )
                raise ValueError(msg)
            message_type_str = message["role"]
            template = message["content"]
        else:
            if len(message) != 2:  # noqa: PLR2004
                msg = f"Expected 2-tuple of (role, template), got {message}"
                raise ValueError(msg)
            message_type_str, template = message

        if isinstance(message_type_str, str):
            message_ = _create_template_from_message_type(
                message_type_str, template, template_format=template_format
            )
        elif (
            hasattr(message_type_str, "model_fields")
            and "type" in message_type_str.model_fields
        ):
            message_type = message_type_str.model_fields["type"].default
            message_ = _create_template_from_message_type(
                message_type, template, template_format=template_format
            )
        else:
            message_ = message_type_str(
                prompt=PromptTemplate.from_template(
                    cast("str", template), template_format=template_format
                )
            )
    else:
        msg = f"Unsupported message type: {type(message)}"
        raise NotImplementedError(msg)

    return message_