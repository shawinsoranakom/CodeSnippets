def _is_composable_message(msg: ForwardMsg) -> bool:
    """True if the ForwardMsg is potentially composable with other ForwardMsgs."""
    if not msg.HasField("delta"):
        # Non-delta messages are never composable.
        return False

    # We never compose add_rows messages in Python, because the add_rows
    # operation can raise errors, and we don't have a good way of handling
    # those errors in the message queue.
    delta_type = msg.delta.WhichOneof("type")
    return delta_type != "add_rows" and delta_type != "arrow_add_rows"