def save_element_message(
    delta_type: str,
    element_proto: Message,
    invoked_dg_id: str,
    used_dg_id: str,
    returned_dg_id: str,
) -> None:
    """Save the message for an element to a thread-local callstack, so it can
    be used later to replay the element when a cache-decorated function's
    execution is skipped.
    """
    MEMO_MESSAGE_CALL_STACK.save_element_message(
        delta_type, element_proto, invoked_dg_id, used_dg_id, returned_dg_id
    )
    SINGLETON_MESSAGE_CALL_STACK.save_element_message(
        delta_type, element_proto, invoked_dg_id, used_dg_id, returned_dg_id
    )