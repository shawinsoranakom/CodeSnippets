def _test_eplb_fml(env, world_size: int, test_config: TestConfig):
    set_env_vars_and_device(env)

    vllm_config = VllmConfig()
    vllm_config.parallel_config.data_parallel_size = world_size
    vllm_config.parallel_config.enable_expert_parallel = True

    with set_current_vllm_config(vllm_config):
        ensure_model_parallel_initialized(
            tensor_model_parallel_size=1, pipeline_model_parallel_size=1
        )

        ep_group = get_dp_group().cpu_group
        ep_rank = torch.distributed.get_rank()

        device = torch.device(f"cuda:{ep_rank}")

        fml_layers = [
            make_fused_moe_layer(ep_rank, layer_idx, test_config).to(device)
            for layer_idx in range(test_config.num_layers)
        ]
        rank_expert_weights = [fml.get_expert_weights() for fml in fml_layers]

        hidden_states = []
        router_logits = []
        for layer_idx in range(test_config.num_layers):
            hidden_states.append(
                torch.randn(
                    (test_config.num_tokens, test_config.hidden_size),
                    dtype=torch.bfloat16,
                    device=device,
                )
            )
            router_logits.append(
                torch.randn(
                    (test_config.num_tokens, test_config.num_experts),
                    dtype=torch.bfloat16,
                    device=device,
                )
            )

        out_before_shuffle = []
        with set_forward_context(
            {},
            num_tokens=test_config.num_tokens,
            num_tokens_across_dp=torch.tensor(
                [test_config.num_tokens] * world_size, device="cpu", dtype=torch.int
            ),
            vllm_config=vllm_config,
        ):
            for lidx, fml in enumerate(fml_layers):
                out_before_shuffle.append(
                    fml(hidden_states[lidx].clone(), router_logits[lidx].clone())
                )

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

        num_global_experts = test_config.num_experts

        logical_to_physical_map_list = []
        for lidx, fml in enumerate(fml_layers):
            physical_to_logical_map = shuffled_indices[lidx].to(device)
            logical_to_physical_map = torch.empty(
                (num_global_experts,), dtype=torch.int32, device=device
            )
            logical_to_physical_map[physical_to_logical_map] = torch.arange(
                0, num_global_experts, dtype=torch.int32, device=device
            )
            logical_to_physical_map_list.append(
                logical_to_physical_map.reshape(num_global_experts, 1)
            )

        logical_to_physical_map = torch.stack(logical_to_physical_map_list)

        for lidx, fml in enumerate(fml_layers):
            logical_replica_count = torch.ones(
                (test_config.num_layers, num_global_experts),
                dtype=torch.int32,
                device=device,
            )
            fml.enable_eplb = True
            fml.set_eplb_state(
                lidx,
                torch.zeros(
                    (test_config.num_layers, num_global_experts),
                    dtype=torch.int32,
                    device=device,
                ),
                logical_to_physical_map,
                logical_replica_count,
            )

        out_after_shuffle = []
        with set_forward_context(
            {},
            num_tokens=test_config.num_tokens,
            num_tokens_across_dp=torch.tensor(
                [test_config.num_tokens] * world_size, device="cpu", dtype=torch.int
            ),
            vllm_config=vllm_config,
        ):
            for lidx, fml in enumerate(fml_layers):
                out_after_shuffle.append(
                    fml(hidden_states[lidx].clone(), router_logits[lidx].clone())
                )

        for lidx in range(test_config.num_layers):
            torch.testing.assert_close(
                out_before_shuffle[lidx], out_after_shuffle[lidx], atol=1e-1, rtol=1e-1
            )