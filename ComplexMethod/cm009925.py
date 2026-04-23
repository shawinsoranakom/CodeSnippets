def _get_messages(inputs: dict[str, Any]) -> dict:
    """Get Chat Messages from inputs.

    Args:
        inputs: The input dictionary.

    Returns:
        A list of chat messages.

    Raises:
        InputFormatError: If the input format is invalid.
    """
    if not inputs:
        msg = "Inputs should not be empty."
        raise InputFormatError(msg)
    input_copy = inputs.copy()
    if "messages" in inputs:
        input_copy["input"] = input_copy.pop("messages")
    elif len(inputs) == 1:
        input_copy["input"] = next(iter(inputs.values()))
    if "input" in input_copy:
        raw_messages = input_copy["input"]
        if isinstance(raw_messages, list) and all(
            isinstance(i, dict) for i in raw_messages
        ):
            raw_messages = [raw_messages]
        if len(raw_messages) == 1:
            input_copy["input"] = messages_from_dict(raw_messages[0])
        else:
            msg = (
                "Batch messages not supported. Please provide a"
                " single list of messages."
            )
            raise InputFormatError(msg)
        return input_copy
    msg = (
        f"Chat Run expects single List[dict] or List[List[dict]] 'messages'"
        f" input. Got {inputs}"
    )
    raise InputFormatError(msg)