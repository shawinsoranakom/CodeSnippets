def create_request(
    request_id: int | None = None,
    num_tokens: int = 10,
    common_prefix_len=0,
    max_tokens: int = 16,
    do_remote_decode: bool = False,
    do_remote_prefill: bool = False,
    num_remote_blocks: int = 3,
    block_size: int = 16,
    hash_fn: Callable = sha256,
) -> Request:
    """Make dummy request for testing."""
    assert num_tokens >= common_prefix_len >= 0

    if request_id is None:
        request_id = next(_request_count)

    global _none_hash_initialized
    if not _none_hash_initialized:
        init_none_hash(hash_fn)
        _none_hash_initialized = True

    kv_transfer_params: dict[str, Any] | None = None

    if do_remote_decode:
        assert not do_remote_prefill
        kv_transfer_params = dict(do_remote_prefill=False, do_remote_decode=True)
    elif do_remote_prefill:
        kv_transfer_params = dict(
            do_remote_prefill=True,
            do_remote_decode=False,
            remote_engine_id="my-engine-id",
            remote_request_id=f"prefill-{request_id}",
            remote_block_ids=list(range(num_remote_blocks)),
            remote_host="my-host",
            remote_port=1234,
        )

    max_tokens = 1 if do_remote_decode else max_tokens
    sampling_params = SamplingParams(max_tokens=max_tokens)
    sampling_params.update_from_generation_config({}, EOS_TOKEN_ID)

    common_prefix = [1] * common_prefix_len if common_prefix_len > 0 else []
    suffix = [i * request_id for i in range(num_tokens - common_prefix_len)]
    prompt_token_ids = common_prefix + suffix

    req = Request(
        request_id=f"id-{request_id}",
        prompt_token_ids=prompt_token_ids,
        sampling_params=sampling_params,
        pooling_params=None,
        mm_features=None,
        block_hasher=get_request_block_hasher(block_size, hash_fn),
    )
    req.kv_transfer_params = kv_transfer_params
    return req