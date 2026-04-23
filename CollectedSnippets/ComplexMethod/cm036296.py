def test_hybrid_attention_mamba_tensor_shapes():
    """
    The GPU model runner creates different views into the
    KVCacheTensors for the attention and mamba layers
    (via _reshape_kv_cache_tensors function). This test verifies
    that the views are compatible: writing a mamba block
    will not corrupt an attention block and vice versa
    """

    set_random_seed(42)

    update_environment_variables(
        {
            "RANK": "0",
            "LOCAL_RANK": "0",
            "WORLD_SIZE": "1",
            "MASTER_ADDR": "localhost",
            "MASTER_PORT": "12345",
        }
    )
    from tests.utils import ensure_current_vllm_config

    with ensure_current_vllm_config():
        init_distributed_environment()
        initialize_model_parallel(tensor_model_parallel_size=1)
    torch.set_default_dtype(torch.float16)

    model_config = ModelConfig(
        model="ibm-granite/granite-4.0-tiny-preview",
        dtype="float16",
    )
    scheduler_config = SchedulerConfig(
        max_num_seqs=10,
        max_num_batched_tokens=512,
        max_model_len=512,
        is_encoder_decoder=model_config.is_encoder_decoder,
    )
    cache_config = CacheConfig(
        block_size=BLOCK_SIZE,
        gpu_memory_utilization=0.9,
        cache_dtype="auto",
    )
    parallel_config = ParallelConfig()
    attention_config = AttentionConfig(backend=AttentionBackendEnum.FLASHINFER)
    vllm_config = VllmConfig(
        model_config=model_config,
        cache_config=cache_config,
        scheduler_config=scheduler_config,
        parallel_config=parallel_config,
        attention_config=attention_config,
    )

    layer_0 = "model.layers.0.self_attn.attn"
    layer_1 = "model.layers.1.self_attn.attn"
    layer_2 = "model.layers.2.mixer"
    layer_3 = "model.layers.3.mixer"
    layer_4 = "model.layers.4.mixer"
    layer_5 = "model.layers.5.mixer"

    with set_current_vllm_config(vllm_config):
        hf_config = vllm_config.model_config.hf_config
        fwd_context = {}
        for key in [layer_0, layer_1]:
            fwd_context[key] = Attention(
                num_heads=model_config.get_num_attention_heads(parallel_config),
                num_kv_heads=model_config.get_num_kv_heads(parallel_config),
                head_size=model_config.get_head_size(),
                scale=1.0,
                prefix=key,
            )
        for key in [layer_2, layer_3, layer_4, layer_5]:
            fwd_context[key] = MambaMixer2(
                hidden_size=hf_config.hidden_size,
                ssm_state_size=hf_config.mamba_d_state,
                conv_kernel_size=hf_config.mamba_d_conv,
                intermediate_size=hf_config.mamba_expand * hf_config.hidden_size,
                use_conv_bias=hf_config.mamba_conv_bias,
                use_bias=hf_config.mamba_proj_bias,
                n_groups=hf_config.mamba_n_groups,
                num_heads=hf_config.mamba_n_heads,
                head_dim=hf_config.mamba_d_head,
                rms_norm_eps=hf_config.rms_norm_eps,
                activation=hf_config.hidden_act,
                cache_config=cache_config,
                model_config=model_config,
                prefix=key,
            )
        # suppress var not used error
        assert fwd_context is not None
        vllm_ctx = vllm_config.compilation_config.static_forward_context

        runner = GPUModelRunner(vllm_config, DEVICE_TYPE)
        current_platform.update_block_size_for_backend(vllm_config)
        kv_cache_spec = runner.get_kv_cache_spec()

        available_memory = 5 * GiB_bytes
        kv_cache_config = get_kv_cache_configs(
            vllm_config, [kv_cache_spec], [available_memory]
        )[0]
        runner.initialize_kv_cache(kv_cache_config)

    # random partition of blocks
    # blocks0 will be assigned to attention layers
    # blocks1 will be assigned to mamba layers
    num_blocks = kv_cache_config.num_blocks
    ind = np.arange(num_blocks)
    np.random.shuffle(ind)
    blocks0, blocks1 = ind[: (num_blocks // 2)], ind[(num_blocks // 2) :]

    attn_shape = vllm_ctx[layer_0].kv_cache.shape
    conv_shape = vllm_ctx[layer_2].kv_cache[0].shape
    ssm_shape = vllm_ctx[layer_2].kv_cache[1].shape

    # assert we are using FlashInfer
    assert attn_shape[0] % num_blocks == 0
    block_split_ratio = attn_shape[0] // num_blocks

    # use small blocks for testing to avoid memory issues
    test_block_size = min(2, len(blocks0), len(blocks1))

    # use non-overlapping blocks to avoid data contamination
    # Split kernel blocks: first half for attention, second half for mamba
    mid_point = num_blocks // 2

    # attention uses kernel blocks from first half (mapped to logical blocks)
    kv_blocks_for_attention = np.array([0, 1])[:test_block_size]

    # mamba uses kernel blocks from second half
    kv_blocks_for_mamba = np.array([mid_point, mid_point + 1])[:test_block_size]

    # create small constant tensors for testing with corrected shapes
    # attention: [block_size, ...] starting from dimension 2
    attn_constant_shape = attn_shape[2:]
    conv_constant_shape = conv_shape[1:]
    ssm_constant_shape = ssm_shape[1:]

    attn_blocks_constant = torch.full(
        (test_block_size, *attn_constant_shape), device=DEVICE_TYPE, fill_value=3.33
    )
    conv_blocks_constant = torch.full(
        (test_block_size, *conv_constant_shape), device=DEVICE_TYPE, fill_value=6.66
    )
    ssm_blocks_constant = torch.full(
        (test_block_size, *ssm_constant_shape), device=DEVICE_TYPE, fill_value=9.99
    )

    # Fill attention blocks with constants using kv block indices
    kernel_blocks_for_attention = kv_blocks_for_attention * block_split_ratio

    for layer in [layer_0, layer_1]:
        # attention: kv_cache[kernel_block_idx, kv_idx, ...]
        for i, kernel_block in enumerate(kernel_blocks_for_attention):
            vllm_ctx[layer].kv_cache[kernel_block, :] = attn_blocks_constant[i]

    # fill mamba blocks with constants using kernel block indices
    for layer in [layer_2, layer_3, layer_4, layer_5]:
        # mamba: kv_cache[component][kernel_block_idx, ...]
        for i, kv_block in enumerate(kv_blocks_for_mamba):
            vllm_ctx[layer].kv_cache[0][kv_block, :] = conv_blocks_constant[i]
            vllm_ctx[layer].kv_cache[1][kv_block, :] = ssm_blocks_constant[i]

    # verify attention and mamba contents are correct
    for layer in [layer_0, layer_1]:
        for i, kernel_block in enumerate(kernel_blocks_for_attention):
            actual_kv = vllm_ctx[layer].kv_cache[kernel_block, :]
            expected = attn_blocks_constant[i]

            # Check K and V separately
            assert torch.equal(actual_kv[0], expected)
            assert torch.equal(actual_kv[1], expected)

    for layer in [layer_2, layer_3, layer_4, layer_5]:
        for i, kv_block in enumerate(kv_blocks_for_mamba):
            actual_conv = vllm_ctx[layer].kv_cache[0][kv_block, :]
            actual_ssm = vllm_ctx[layer].kv_cache[1][kv_block, :]
            expected_conv = conv_blocks_constant[i]
            expected_ssm = ssm_blocks_constant[i]

            assert torch.equal(actual_conv, expected_conv)
            assert torch.equal(actual_ssm, expected_ssm)

    for layer in [layer_2, layer_3, layer_4, layer_5]:
        for i, kv_block in enumerate(kv_blocks_for_mamba):
            actual_conv = vllm_ctx[layer].kv_cache[0][kv_block, :]
            actual_ssm = vllm_ctx[layer].kv_cache[1][kv_block, :]
            expected_conv = conv_blocks_constant[i]
            expected_ssm = ssm_blocks_constant[i]
            assert torch.equal(actual_conv, expected_conv)
            assert torch.equal(actual_ssm, expected_ssm)