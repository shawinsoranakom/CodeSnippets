def update_hash(
    val: Any,
    hasher,
    hash_reason: HashReason,
    hash_source: Callable[..., Any],
    context: Optional[Context] = None,
    hash_funcs: Optional[HashFuncsDict] = None,
) -> None:
    """Updates a hashlib hasher with the hash of val.

    This is the main entrypoint to hashing.py.
    """
    hash_stacks.current.hash_reason = hash_reason
    hash_stacks.current.hash_source = hash_source

    ch = _CodeHasher(hash_funcs)
    ch.update(hasher, val, context)