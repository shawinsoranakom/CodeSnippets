def save_block_message(
    block_proto: Block,
    invoked_dg_id: str,
    used_dg_id: str,
    returned_dg_id: str,
) -> None:
    """Save the message for a block to a thread-local callstack, so it can
    be used later to replay the block when a cache-decorated function's
    execution is skipped.
    """
    MEMO_MESSAGE_CALL_STACK.save_block_message(
        block_proto, invoked_dg_id, used_dg_id, returned_dg_id
    )
    SINGLETON_MESSAGE_CALL_STACK.save_block_message(
        block_proto, invoked_dg_id, used_dg_id, returned_dg_id
    )