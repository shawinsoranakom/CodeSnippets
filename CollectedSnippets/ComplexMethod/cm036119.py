def test_causal_backend_correctness(
    default_vllm_config, batch_spec_name: str, model: str, tensor_parallel_size: int
):
    """Test backend's correctness with causal attention."""

    def causal_mask_mod(
        b: torch.Tensor,
        h: torch.Tensor,
        q_idx: torch.Tensor,
        kv_idx: torch.Tensor,
        *,
        context_len: int,
    ):
        return (q_idx + context_len) >= kv_idx

    batch_spec = BATCH_SPECS[batch_spec_name]
    LARGE_BLOCK_BACKENDS = (
        [AttentionBackendEnum.FLEX_ATTENTION]
        if is_torch_equal_or_newer("2.9.0.dev0")
        else []
    )

    if current_platform.is_rocm():
        SMALL_BLOCK_BACKENDS = [
            x
            for x in BACKENDS_TO_TEST
            if (
                x not in LARGE_BLOCK_BACKENDS
                and x is not AttentionBackendEnum.FLASH_ATTN
            )
        ]
    else:
        SMALL_BLOCK_BACKENDS = [
            x for x in BACKENDS_TO_TEST if x not in LARGE_BLOCK_BACKENDS
        ]

    _test_backend_correctness(
        batch_spec,
        model,
        SMALL_BLOCK_BACKENDS,
        causal_mask_mod,
        tensor_parallel_size=tensor_parallel_size,
    )

    # Fast FlexAttention needs to run with block_size=128
    if LARGE_BLOCK_BACKENDS:
        _test_backend_correctness(
            batch_spec,
            model,
            LARGE_BLOCK_BACKENDS,
            causal_mask_mod,
            block_size=128,
            tensor_parallel_size=tensor_parallel_size,
        )