def _test_backend_correctness(
    batch_spec: BatchSpec,
    model: str,
    backend_to_test: list[AttentionBackendEnum | str],
    mask_mod,
    *,
    causal: bool = True,
    attn_type: AttentionType = AttentionType.DECODER,
    block_size: int = 16,
    atol: float = 1e-2,
    rtol: float = 1e-2,
    tensor_parallel_size: int = 1,
):
    """
    Test that all backends produce similar outputs to a reference implementation
    using torch.nn.functional.scaled_dot_product_attention.

    This test works by:
    1. Generating a batch of sequences with specified context and query lengths.
    2. Computing a ground-truth attention output using torch.sdpa on
       contiguous Q, K, and V tensors.
    3. Simulating vLLM's paged KV cache: It takes the context portion of the
       K/V tensors and manually places them into a paged buffer according to
       the test's (randomly generated) block table.
    4. Running each vLLM attention backend with the new queries and the
       simulated paged KV cache.
    5. Comparing the vLLM backend's output to the ground-truth SDPA output.

    Note: When tensor_parallel_size > 1, we simulate the head partitioning
    by overriding the model config to use fewer heads, without requiring
    multiple GPUs. This tests that backends work correctly with different
    head counts.
    """
    set_random_seed(42)

    hf_config_override = None
    if tensor_parallel_size > 1:
        from vllm.config import ModelConfig

        temp_config = ModelConfig(model=model, max_model_len=1)
        original_num_heads = temp_config.hf_text_config.num_attention_heads
        original_num_kv_heads = getattr(
            temp_config.hf_text_config, "num_key_value_heads", None
        )
        hf_config_override = {
            "num_attention_heads": original_num_heads // tensor_parallel_size,
        }
        if original_num_kv_heads is not None:
            hf_config_override["num_key_value_heads"] = max(
                1, original_num_kv_heads // tensor_parallel_size
            )

    vllm_config = create_vllm_config(
        model_name=model,
        tensor_parallel_size=1,  # Always use TP=1 to avoid multi-GPU requirements
        max_model_len=max(batch_spec.seq_lens),
        block_size=block_size,
        num_gpu_blocks=8192,
        hf_config_override=hf_config_override,
    )
    device = torch.device(f"{DEVICE_TYPE}:0")

    kv_cache_spec = create_standard_kv_cache_spec(vllm_config, attn_type)

    # 1. Setup
    batch_size = batch_spec.batch_size
    seq_lens = batch_spec.seq_lens
    query_lens = batch_spec.query_lens
    num_q_heads = vllm_config.model_config.get_num_attention_heads(
        vllm_config.parallel_config
    )
    num_kv_heads = vllm_config.model_config.get_num_kv_heads(
        vllm_config.parallel_config
    )
    head_size = vllm_config.model_config.get_head_size()
    sliding_window = vllm_config.model_config.get_sliding_window()
    dtype = _convert_dtype_to_torch(vllm_config.model_config.dtype)
    block_size = vllm_config.cache_config.block_size
    scale = 1.0 / (head_size**0.5)

    # 2. Generate data and compute SDPA reference output
    all_q_vllm, all_k_vllm, all_v_vllm = [], [], []
    all_sdpa_outputs = []
    k_contexts, v_contexts = [], []

    for i in range(batch_size):
        s_len = seq_lens[i]
        q_len = query_lens[i]
        context_len = s_len - q_len

        # Generate Q, K, V for the whole sequence to be used in SDPA
        q = torch.randn(q_len, num_q_heads, head_size, dtype=dtype, device=device)
        k_full = torch.randn(s_len, num_kv_heads, head_size, dtype=dtype, device=device)
        v_full = torch.randn(s_len, num_kv_heads, head_size, dtype=dtype, device=device)

        # SDPA expects (N, H, L, D), so unsqueeze batch and permute
        q_sdpa_in = q.unsqueeze(0).transpose(1, 2)
        k_sdpa_in = k_full.unsqueeze(0).transpose(1, 2)
        v_sdpa_in = v_full.unsqueeze(0).transpose(1, 2)

        if num_q_heads != num_kv_heads:
            assert num_q_heads % num_kv_heads == 0, (
                f"num_q_heads ({num_q_heads}) must be divisible by "
                f"num_kv_heads ({num_kv_heads})"
            )
            repeats = num_q_heads // num_kv_heads
            k_sdpa_in = k_sdpa_in.repeat_interleave(repeats, dim=1)
            v_sdpa_in = v_sdpa_in.repeat_interleave(repeats, dim=1)

        # Create causal mask: query token i attends to positions 0 to
        #  (context_len + i)
        kv_len = s_len

        final_mask_mod = partial(mask_mod, context_len=context_len)
        block_mask = create_block_mask(
            final_mask_mod, B=None, H=None, Q_LEN=q_len, KV_LEN=kv_len, device=device
        )
        sdpa_out_i = flex_attention(
            q_sdpa_in,
            k_sdpa_in,
            v_sdpa_in,
            block_mask=block_mask,
            scale=scale,
            enable_gqa=True,
        )

        all_sdpa_outputs.append(sdpa_out_i.transpose(1, 2).squeeze(0))

        # Inputs for vLLM backends are just the new tokens
        all_q_vllm.append(q)
        all_k_vllm.append(k_full[context_len:])
        all_v_vllm.append(v_full[context_len:])

        # Contextual K/V data used to populate the paged cache
        k_contexts.append(k_full[:context_len])
        v_contexts.append(v_full[:context_len])

    query_vllm = torch.cat(all_q_vllm, dim=0)
    key_vllm = torch.cat(all_k_vllm, dim=0)
    value_vllm = torch.cat(all_v_vllm, dim=0)
    sdpa_output = torch.cat(all_sdpa_outputs, dim=0)

    common_attn_metadata = create_common_attn_metadata(
        batch_spec, vllm_config.cache_config.block_size, device
    )
    common_attn_metadata.causal = causal

    # 3. Simulate Paged KV Cache and a realistic slot_mapping
    kv_cache = create_and_prepopulate_kv_cache(
        k_contexts=k_contexts,
        v_contexts=v_contexts,
        block_size=block_size,
        num_kv_heads=num_kv_heads,
        head_size=head_size,
        dtype=dtype,
        device=device,
        num_blocks=vllm_config.cache_config.num_gpu_blocks or 1000,
        common_attn_metadata=common_attn_metadata,
        randomize_blocks=True,
    )

    # 4. Run vLLM backends and compare
    # Note: flex_attention has known Triton kernel compatibility issues
    # with test infrastructures
    for backend_name in backend_to_test:
        # FlashAttentionm + FlexAttention:
        #   [2, num_blocks, block_size, num_kv_heads, head_size]
        # FlashInfer + Triton:
        #   [num_blocks, 2, block_size, num_kv_heads, head_size]
        # Select the appropriate KV cache format for each backend
        kv_cache_for_backend = kv_cache
        reset_kv_cache_layout = False
        if backend_name in (
            AttentionBackendEnum.FLASHINFER,
            AttentionBackendEnum.TRITON_ATTN,
        ):
            kv_cache_for_backend = kv_cache.transpose(0, 1)

        if backend_name == AttentionBackendEnum.FLASHINFER:
            # For FlashInfer default to HND layout and
            kv_cache_for_backend = (
                kv_cache_for_backend.transpose(2, 3).contiguous().transpose(2, 3)
            )
            set_kv_cache_layout("HND")
            reset_kv_cache_layout = True
        elif backend_name == AttentionBackendEnum.TRITON_ATTN:
            kv_cache_for_backend = kv_cache_for_backend.contiguous()

        try:
            backend_output = run_attention_backend(
                backend_name,
                kv_cache_spec,
                ["placeholder"],
                vllm_config,
                device,
                common_attn_metadata,
                query_vllm,
                key_vllm,
                value_vllm,
                kv_cache_for_backend,
                sliding_window=sliding_window,
                attn_type=attn_type,
            )
        finally:
            if reset_kv_cache_layout:
                set_kv_cache_layout(None)

        # Check shape and dtype consistency
        assert backend_output.shape == sdpa_output.shape, (
            f"[{backend_name}] shape {backend_output.shape} != "
            f"SDPA shape {sdpa_output.shape}"
        )
        assert backend_output.dtype == sdpa_output.dtype, (
            f"[{backend_name}] dtype {backend_output.dtype} != "
            f"SDPA dtype {sdpa_output.dtype}"
        )

        assert torch.isfinite(backend_output).all(), (
            f"[{backend_name}] produced non-finite values"
        )

        # Check numerical similarity
        def error_msg(msg: str, backend_name: str):
            return f"[{backend_name}] output differs from SDPA baseline. {msg}"

        torch.testing.assert_close(
            backend_output,
            sdpa_output,
            rtol=rtol,
            atol=atol,
            msg=partial(error_msg, backend_name=backend_name),
        )