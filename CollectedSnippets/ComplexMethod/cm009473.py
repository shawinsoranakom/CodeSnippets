def _create_template_from_message_type(
    message_type: str,
    template: str | list,
    template_format: PromptTemplateFormat = "f-string",
) -> BaseMessagePromptTemplate:
    """Create a message prompt template from a message type and template string.

    Args:
        message_type: The type of the message template (e.g., `'human'`, `'ai'`, etc.)
        template: The template string.
        template_format: Format of the template.

    Returns:
        A message prompt template of the appropriate type.

    Raises:
        ValueError: If unexpected message type.
    """
    if message_type in {"human", "user"}:
        message: BaseMessagePromptTemplate = HumanMessagePromptTemplate.from_template(
            template, template_format=template_format
        )
    elif message_type in {"ai", "assistant"}:
        message = AIMessagePromptTemplate.from_template(
            cast("str", template), template_format=template_format
        )
    elif message_type == "system":
        message = SystemMessagePromptTemplate.from_template(
            cast("str", template), template_format=template_format
        )
    elif message_type == "placeholder":
        if isinstance(template, str):
            if template[0] != "{" or template[-1] != "}":
                msg = (
                    f"Invalid placeholder template: {template}."
                    " Expected a variable name surrounded by curly braces."
                )
                raise ValueError(msg)
            var_name = template[1:-1]
            message = MessagesPlaceholder(variable_name=var_name, optional=True)
        else:
            try:
                var_name_wrapped, is_optional = template
            except ValueError as e:
                msg = (
                    "Unexpected arguments for placeholder message type."
                    " Expected either a single string variable name"
                    " or a list of [variable_name: str, is_optional: bool]."
                    f" Got: {template}"
                )
                raise ValueError(msg) from e

            if not isinstance(is_optional, bool):
                msg = f"Expected is_optional to be a boolean. Got: {is_optional}"
                raise ValueError(msg)  # noqa: TRY004

            if not isinstance(var_name_wrapped, str):
                msg = f"Expected variable name to be a string. Got: {var_name_wrapped}"
                raise ValueError(msg)  # noqa: TRY004
            if var_name_wrapped[0] != "{" or var_name_wrapped[-1] != "}":
                msg = (
                    f"Invalid placeholder template: {var_name_wrapped}."
                    " Expected a variable name surrounded by curly braces."
                )
                raise ValueError(msg)
            var_name = var_name_wrapped[1:-1]

            message = MessagesPlaceholder(variable_name=var_name, optional=is_optional)
    else:
        msg = (
            f"Unexpected message type: {message_type}. Use one of 'human',"
            f" 'user', 'ai', 'assistant', or 'system'."
        )
        raise ValueError(msg)
    return message