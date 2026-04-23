def get_code_state() -> defaultdict[CodeId, CodeState]:
    global _CODE_STATE, _INIT_CODE_STATE
    if _CODE_STATE is not None:
        return _CODE_STATE

    # Initialize it (even if we don't look up profile)
    _CODE_STATE = defaultdict(CodeState)

    cache_key = get_cache_key()
    if cache_key is None:
        return _CODE_STATE

    # Attempt local
    local_code_state = get_local_code_state(cache_key)

    # Attempt remote
    if local_code_state is None:
        get_remote_code_state(cache_key)

    # Attempt additional remote if neither local/default remote succeeded
    if (
        not _CODE_STATE
        and (sticky_read := torch.compiler.config.pgo_extra_read_key) is not None
    ):
        extra_read_key = get_extra_cache_key(sticky_read)
        if extra_read_key is not None:
            get_extra_remote_code_state(extra_read_key)

    log.info("get_code_state using default")

    assert _CODE_STATE is not None
    return _CODE_STATE