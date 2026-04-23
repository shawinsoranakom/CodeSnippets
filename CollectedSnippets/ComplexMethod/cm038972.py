def _create_backend_impl(
    backend_cfg: dict,
    mla_dims: dict,
    vllm_config: VllmConfig,
    device: torch.device,
    max_num_tokens: int = 8192,
    index_topk: int | None = None,
    kv_cache_dtype: str = "auto",
):
    """
    Create backend implementation instance.

    Args:
        backend_cfg: Backend configuration dict from _get_backend_config()
        mla_dims: MLA dimension configuration
        vllm_config: VllmConfig instance
        device: Target device
        max_num_tokens: Maximum number of tokens for sparse indexer buffer
        index_topk: Topk value for sparse MLA backends

    Returns:
        Tuple of (impl, layer, builder_instance, indexer)
    """
    # Get classes from backend config (already resolved by _get_backend_config)
    impl_class = backend_cfg["impl_class"]
    builder_class = backend_cfg["builder_class"]

    # Calculate scale
    scale = 1.0 / np.sqrt(mla_dims["qk_nope_head_dim"] + mla_dims["qk_rope_head_dim"])

    # Create mock kv_b_proj layer for prefill mode
    mock_kv_b_proj = MockKVBProj(
        num_heads=mla_dims["num_q_heads"],
        qk_nope_head_dim=mla_dims["qk_nope_head_dim"],
        v_head_dim=mla_dims["v_head_dim"],
    )

    # Create indexer for sparse backends
    indexer = None
    if backend_cfg.get("is_sparse", False):
        if index_topk is None:
            index_topk = 2048  # Default topk for sparse MLA
        indexer = MockIndexer(
            max_num_tokens=max_num_tokens,
            topk_tokens=index_topk,
            device=device,
        )

    # Build impl kwargs
    impl_kwargs = {
        "num_heads": mla_dims["num_q_heads"],
        "head_size": mla_dims["head_dim"],
        "scale": scale,
        "num_kv_heads": mla_dims["num_kv_heads"],
        "alibi_slopes": None,
        "sliding_window": None,
        "kv_cache_dtype": kv_cache_dtype,
        "logits_soft_cap": None,
        "attn_type": "decoder",
        "kv_sharing_target_layer_name": None,
        "q_lora_rank": None,
        "kv_lora_rank": mla_dims["kv_lora_rank"],
        "qk_nope_head_dim": mla_dims["qk_nope_head_dim"],
        "qk_rope_head_dim": mla_dims["qk_rope_head_dim"],
        "qk_head_dim": mla_dims["qk_nope_head_dim"] + mla_dims["qk_rope_head_dim"],
        "v_head_dim": mla_dims["v_head_dim"],
        "kv_b_proj": mock_kv_b_proj,
    }

    # Add indexer for sparse backends
    if indexer is not None:
        impl_kwargs["indexer"] = indexer

    # Create impl
    impl = impl_class(**impl_kwargs)

    # Initialize DCP attributes
    if not hasattr(impl, "dcp_world_size") or impl.dcp_world_size in (None, -1):
        impl.dcp_world_size = 1
        impl.dcp_rank = 0

    # Create KV cache spec for MockLayer
    from vllm.v1.kv_cache_interface import FullAttentionSpec

    kv_cache_spec = FullAttentionSpec(
        block_size=backend_cfg["block_size"] or vllm_config.cache_config.block_size,
        num_kv_heads=1,  # MLA uses 1 KV head
        head_size=576,  # MLA head dim
        dtype=torch.bfloat16,
    )

    # Create mock layer
    layer = MockLayer(device, impl=impl, kv_cache_spec=kv_cache_spec)

    # Create builder instance if needed
    builder_instance = None
    if builder_class:
        # Populate static_forward_context so builder can find the layer
        # MockLayer inherits from AttentionLayerBase, so isinstance checks pass
        vllm_config.compilation_config.static_forward_context = {"placeholder": layer}

        builder_instance = builder_class(
            kv_cache_spec=kv_cache_spec,
            layer_names=["placeholder"],
            vllm_config=vllm_config,
            device=device,
        )

    return impl, layer, builder_instance, indexer