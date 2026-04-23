def test_fsdp2_meta_loading_buffers_and_tied_weights():
    """Verify non-persistent buffers and tied weights consistency after meta load."""
    # 1. Initialize DistributedInterface for single process
    DistributedInterface()

    # 2. Build FSDP2Engine config
    engine = FSDP2Engine(
        {
            "name": "fsdp2",
            "mixed_precision": "bf16",
            "reshard_after_forward": True,
            "offload_params": False,
            "pin_memory": False,
            "dcp_path": None,
        }
    )

    config = AutoConfig.from_pretrained(TINY_MODEL)

    # --- NORMAL PATH ---
    normal_args, *_ = get_args(dict(model=TINY_MODEL, init_config=None))
    normal_engine = ModelEngine(model_args=normal_args)
    normal_model = normal_engine.model.to(torch.bfloat16)

    normal_model = engine.shard_model(normal_model)
    normal_non_persistent = collect_non_persistent_buffers(normal_model)

    del normal_model

    # --- META PATH ---
    meta_args, *_ = get_args(dict(model=TINY_MODEL, init_config={"name": "init_on_meta"}))
    meta_model_engine = ModelEngine(model_args=meta_args)
    meta_model = meta_model_engine.model

    assert meta_model.device.type == "meta", "Model should be on meta device"

    # Process meta device: save buffers -> tie_weights -> load from checkpoint -> restore buffers
    meta_model = engine.shard_model(meta_model)
    meta_non_persistent = collect_non_persistent_buffers(meta_model)

    # 3. Tied weights (embed_tokens.weight and lm_head.weight)

    tie_word_embeddings = getattr(config, "tie_word_embeddings", False)
    if tie_word_embeddings:
        assert meta_model.lm_head.weight is meta_model.model.embed_tokens.weight, (
            "Weights should be tied after loading"
        )

    del meta_model

    # 4. Non-persistent buffers (e.g., inv_freq)
    normal_buf_keys = set(normal_non_persistent.keys())
    meta_buf_keys = set(meta_non_persistent.keys())
    assert normal_buf_keys == meta_buf_keys, "Non-persistent buffer keys mismatch"

    for key in sorted(normal_buf_keys & meta_buf_keys):
        nb = normal_non_persistent[key]
        mb = meta_non_persistent[key]
        assert nb.shape == mb.shape, f"Buffer shape mismatch: {key}"
        assert torch.allclose(nb.float(), mb.float(), atol=1e-5), f"Buffer value mismatch: {key}"