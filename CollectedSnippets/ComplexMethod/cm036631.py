def _test_eplb_fml(env, world_size: int, test_config: TestConfig):
    # Initialize model parallel (using tensor parallel as an entrypoint
    # to expert parallel)
    set_env_vars_and_device(env)

    vllm_config = VllmConfig()
    vllm_config.parallel_config.tensor_parallel_size = world_size
    vllm_config.parallel_config.enable_expert_parallel = True

    with set_current_vllm_config(vllm_config):
        ensure_model_parallel_initialized(
            tensor_model_parallel_size=world_size, pipeline_model_parallel_size=1
        )

        ep_group = get_tp_group().cpu_group
        ep_rank = torch.distributed.get_rank()

        fml_layers = [
            make_fused_moe_layer(ep_rank, layer_idx, test_config)
            for layer_idx in range(test_config.num_layers)
        ]
        rank_expert_weights = [fml.get_expert_weights() for fml in fml_layers]

        indices = torch.zeros(
            test_config.num_layers, test_config.num_experts, dtype=torch.long
        )
        for lidx in range(test_config.num_layers):
            indices[lidx] = torch.Tensor(range(test_config.num_experts))

        shuffled_indices = torch.zeros_like(indices)
        for lidx in range(test_config.num_layers):
            shuffled_indices[lidx] = torch.randperm(test_config.num_experts)

        rearrange_expert_weights_inplace(
            indices,
            shuffled_indices,
            rank_expert_weights,
            ep_group,
            is_profile=False,
        )

        num_local_experts = test_config.num_local_experts
        num_global_experts = test_config.num_experts
        for lidx, fml in enumerate(fml_layers):
            for name, w in fml.named_parameters():
                for e in range(num_local_experts):
                    g_e = shuffled_indices[lidx][ep_rank * num_local_experts + e]
                    ref = make_expert_weights(
                        layer_idx=lidx,
                        global_expert_idx=int(g_e.item()),
                        global_num_experts=num_global_experts,
                        tensor_shape=w[e].shape,
                        tensor_dtype=w[e].dtype,
                        tensor_device=w[e].device,
                        is_column_major=not w[e].is_contiguous(),
                    )
                    assert w[e].shape == ref.shape and w[e].stride() == ref.stride(), (
                        f"w[{e}] {w[e].size()} {w[e].stride()} vs "
                        f"ref {ref.size()} {ref.stride()}"
                    )
                    torch.testing.assert_close(w[e], ref)