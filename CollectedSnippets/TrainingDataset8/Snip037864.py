def populate_hash_if_needed(msg: ForwardMsg) -> str:
    """Computes and assigns the unique hash for a ForwardMsg.

    If the ForwardMsg already has a hash, this is a no-op.

    Parameters
    ----------
    msg : ForwardMsg

    Returns
    -------
    string
        The message's hash, returned here for convenience. (The hash
        will also be assigned to the ForwardMsg; callers do not need
        to do this.)

    """
    if msg.hash == "":
        # Move the message's metadata aside. It's not part of the
        # hash calculation.
        metadata = msg.metadata
        msg.ClearField("metadata")

        # MD5 is good enough for what we need, which is uniqueness.
        hasher = hashlib.md5()
        hasher.update(msg.SerializeToString())
        msg.hash = hasher.hexdigest()

        # Restore metadata.
        msg.metadata.CopyFrom(metadata)

    return msg.hash