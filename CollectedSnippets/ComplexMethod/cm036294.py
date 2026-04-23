def test_init_kv_cache_without_kv_sharing(default_vllm_config):
    torch.set_default_dtype(torch.float16)
    layer_0 = "model.layers.0.self_attn.attn"
    layer_1 = "model.layers.1.self_attn.attn"
    vllm_config = get_vllm_config()
    with set_current_vllm_config(vllm_config):
        fwd_context = {
            layer_0: Attention(
                num_heads=8,
                head_size=64,
                scale=1.0,
                prefix=layer_0,
            ),
            layer_1: Attention(
                num_heads=8,
                head_size=64,
                scale=1.0,
                prefix=layer_1,
            ),
        }
        # suppress var not used error
        assert fwd_context is not None
    # Set high context length to test max context length estimation
    vllm_config.model_config.max_model_len = 3_000_000
    vllm_ctx = vllm_config.compilation_config.static_forward_context
    runner = GPUModelRunner(vllm_config, DEVICE_TYPE)
    kv_cache_spec = runner.get_kv_cache_spec()
    assert len(kv_cache_spec) == 2
    assert len(runner.shared_kv_cache_layers) == 0

    available_memory = 20 * GiB_bytes
    # page size for layer 0's kv_cache_spec is 32KB
    num_expected_blocks = 327680  # 20GB / 32KB / 2 (num layers)
    kv_cache_config = get_kv_cache_configs(
        vllm_config, [kv_cache_spec], [available_memory]
    )[0]
    assert kv_cache_config.num_blocks == num_expected_blocks
    assert len(kv_cache_config.kv_cache_tensors) == 2
    assert kv_cache_config.kv_cache_tensors[0].size == available_memory // 2
    assert kv_cache_config.kv_cache_tensors[1].size == available_memory // 2

    max_context_len = estimate_max_model_len(vllm_config, kv_cache_spec, 5 * GiB_bytes)
    # max context len with KV sharing should be 2x as large as without
    assert max_context_len == 1310720

    # important: override tensor size to prevent large mem alloc during test
    # this will only allocate 2 block worth of memory (2 * 32kb)
    kv_cache_config.num_blocks = 1
    for kv_cache_tensor in kv_cache_config.kv_cache_tensors:
        kv_cache_tensor.size = kv_cache_spec[
            kv_cache_tensor.shared_by[0]
        ].page_size_bytes

    runner.initialize_kv_cache(kv_cache_config)

    layer_0_kv = vllm_ctx[layer_0].kv_cache
    layer_1_kv = vllm_ctx[layer_1].kv_cache
    # check layer 1 kv cache does NOT share memory with layer 0
    assert id(layer_1_kv) != id(layer_0_kv)

    # check layer 1 added to kv cache group's layer names
    assert len(kv_cache_config.kv_cache_groups) == 1
    assert len(kv_cache_config.kv_cache_groups[0].layer_names) == 2
    assert kv_cache_config.kv_cache_groups[0].layer_names[0] == layer_0
    assert kv_cache_config.kv_cache_groups[0].layer_names[1] == layer_1