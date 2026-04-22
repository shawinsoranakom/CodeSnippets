def serialize_forward_msg(msg: ForwardMsg) -> bytes:
    """Serialize a ForwardMsg to send to a client.

    If the message is too large, it will be converted to an exception message
    instead.
    """
    populate_hash_if_needed(msg)
    msg_str = msg.SerializeToString()

    if len(msg_str) > get_max_message_size_bytes():
        import streamlit.elements.exception as exception

        # Overwrite the offending ForwardMsg.delta with an error to display.
        # This assumes that the size limit wasn't exceeded due to metadata.
        exception.marshall(msg.delta.new_element.exception, MessageSizeError(msg_str))
        msg_str = msg.SerializeToString()

    return msg_str