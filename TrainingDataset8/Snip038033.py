def is_cacheable_msg(msg: ForwardMsg) -> bool:
    """True if the given message qualifies for caching."""
    if msg.WhichOneof("type") in {"ref_hash", "initialize"}:
        # Some message types never get cached
        return False
    return msg.ByteSize() >= int(config.get_option("global.minCachedMessageSize"))