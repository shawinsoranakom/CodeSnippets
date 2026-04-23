def accumulate_usage(existing: Usage | None, new: Usage | None) -> Usage | None:
    """Accumulate usage data across multiple chunks.

    Some providers (e.g. Anthropic) split usage across chunks:
    message_start has input_tokens, message_delta has output_tokens.

    Args:
        existing: Previously accumulated usage, or None.
        new: New usage from the current chunk, or None.

    Returns:
        Accumulated Usage, or None if both inputs are None.
    """
    if new is None:
        return existing
    if existing is None:
        return new

    input_tokens = existing.input_tokens or 0
    output_tokens = existing.output_tokens or 0

    new_input = new.input_tokens or 0
    new_output = new.output_tokens or 0

    if new_input:
        input_tokens += new_input
    if new_output:
        output_tokens += new_output

    return Usage(
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        total_tokens=input_tokens + output_tokens,
    )