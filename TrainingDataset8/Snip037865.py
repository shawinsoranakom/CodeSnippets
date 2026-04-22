def create_reference_msg(msg: ForwardMsg) -> ForwardMsg:
    """Create a ForwardMsg that refers to the given message via its hash.

    The reference message will also get a copy of the source message's
    metadata.

    Parameters
    ----------
    msg : ForwardMsg
        The ForwardMsg to create the reference to.

    Returns
    -------
    ForwardMsg
        A new ForwardMsg that "points" to the original message via the
        ref_hash field.

    """
    ref_msg = ForwardMsg()
    ref_msg.ref_hash = populate_hash_if_needed(msg)
    ref_msg.metadata.CopyFrom(msg.metadata)
    return ref_msg