def _ensure_tool_pairs_intact(
    recent_messages: list[dict],
    all_messages: list[dict],
    start_index: int,
) -> list[dict]:
    """
    Ensure tool_call/tool_response pairs stay together after slicing.

    When slicing messages for context compaction, a naive slice can separate
    an assistant message containing tool_calls from its corresponding tool
    response messages. This causes API validation errors (e.g., Anthropic's
    "unexpected tool_use_id found in tool_result blocks").

    This function checks for orphan tool responses in the slice and extends
    backwards to include their corresponding assistant messages.

    Supports both formats:
    - OpenAI: tool_calls array + role="tool" responses
    - Anthropic: tool_use blocks + tool_result blocks

    Args:
        recent_messages: The sliced messages to validate
        all_messages: The complete message list (for looking up missing assistants)
        start_index: The index in all_messages where recent_messages begins

    Returns:
        A potentially extended list of messages with tool pairs intact
    """
    if not recent_messages:
        return recent_messages

    # Collect all tool_call_ids from assistant messages in the slice
    available_tool_call_ids: set[str] = set()
    for msg in recent_messages:
        available_tool_call_ids |= _extract_tool_call_ids_from_message(msg)

    # Find orphan tool responses (responses whose tool_call_id is missing)
    orphan_tool_call_ids: set[str] = set()
    for msg in recent_messages:
        response_ids = _extract_tool_response_ids_from_message(msg)
        for tc_id in response_ids:
            if tc_id not in available_tool_call_ids:
                orphan_tool_call_ids.add(tc_id)

    if not orphan_tool_call_ids:
        # No orphans, slice is valid
        return recent_messages

    # Find the assistant messages that contain the orphan tool_call_ids
    # Search backwards from start_index in all_messages
    messages_to_prepend: list[dict] = []
    for i in range(start_index - 1, -1, -1):
        msg = all_messages[i]
        msg_tool_ids = _extract_tool_call_ids_from_message(msg)
        if msg_tool_ids & orphan_tool_call_ids:
            # This assistant message has tool_calls we need
            # Also collect its contiguous tool responses that follow it
            assistant_and_responses: list[dict] = [msg]

            # Scan forward from this assistant to collect tool responses
            for j in range(i + 1, start_index):
                following_msg = all_messages[j]
                following_response_ids = _extract_tool_response_ids_from_message(
                    following_msg
                )
                if following_response_ids and following_response_ids & msg_tool_ids:
                    assistant_and_responses.append(following_msg)
                elif not _is_tool_response_message(following_msg):
                    # Stop at first non-tool-response message
                    break

            # Prepend the assistant and its tool responses (maintain order)
            messages_to_prepend = assistant_and_responses + messages_to_prepend
            # Mark these as found
            orphan_tool_call_ids -= msg_tool_ids
            # Also add this assistant's tool_call_ids to available set
            available_tool_call_ids |= msg_tool_ids

        if not orphan_tool_call_ids:
            # Found all missing assistants
            break

    if orphan_tool_call_ids:
        # Some tool_call_ids couldn't be resolved - remove those tool responses
        # This shouldn't happen in normal operation but handles edge cases
        logger.warning(
            f"Could not find assistant messages for tool_call_ids: {orphan_tool_call_ids}. "
            "Removing orphan tool responses."
        )
        recent_messages = _remove_orphan_tool_responses(
            recent_messages, orphan_tool_call_ids
        )

    if messages_to_prepend:
        logger.info(
            f"Extended recent messages by {len(messages_to_prepend)} to preserve "
            f"tool_call/tool_response pairs"
        )
        return messages_to_prepend + recent_messages

    return recent_messages