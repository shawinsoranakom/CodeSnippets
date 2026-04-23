def test_column_parallel_packed(
    default_vllm_config, dist_init, num_loras, repeats, fully_shard, device, stage
) -> None:
    if current_platform.is_cuda_alike():
        torch.accelerator.set_device_index(device)

    max_loras = 8
    torch.set_default_device(device)
    lora_config = LoRAConfig(
        max_loras=max_loras,
        max_lora_rank=8,
        fully_sharded_loras=fully_shard,
        lora_dtype=torch.float16,
    )
    punica_wrapper = get_punica_wrapper(8192, 256, device, lora_config=lora_config)
    assert check_punica_wrapper(punica_wrapper)

    def create_column_parallel_packed_layer(idx: int = 0):
        if repeats == 2:
            linear = MergedColumnParallelLinear(
                4096,
                [4096] * repeats,
                bias=False,
                params_dtype=torch.float16,
                prefix=f"layer_{idx}",
            )
            linear.weight.data = torch.rand_like(linear.weight.data)
            lora_linear = (
                MergedColumnParallelLinearWithLoRA(linear)
                if not fully_shard
                else MergedColumnParallelLinearWithShardedLoRA(linear)
            )
        elif repeats == 3:
            linear = QKVParallelLinear(
                4096,
                64,
                32,
                bias=False,
                params_dtype=torch.float16,
                prefix=f"layer_{idx}",
            )
            linear.weight.data = torch.rand_like(linear.weight.data)
            lora_linear = (
                MergedQKVParallelLinearWithLoRA(linear)
                if not fully_shard
                else MergedQKVParallelLinearWithShardedLoRA(linear)
            )
        else:
            linear = QKVParallelLinear(
                4096,
                64,
                32,
                bias=False,
                params_dtype=torch.float16,
                prefix=f"layer_{idx}",
            )
            linear.weight.data = torch.rand_like(linear.weight.data)
            lora_linear = (
                QKVParallelLinearWithLoRA(linear)
                if not fully_shard
                else QKVParallelLinearWithShardedLoRA(linear)
            )

        @dataclass
        class FakeConfig:
            hidden_size = 4096
            num_key_value_heads = 32
            num_attention_heads = 32

        n_slices = repeats
        lora_linear.create_lora_weights(
            max_loras, lora_config, model_config=FakeConfig()
        )
        assert (
            lora_linear.n_slices
            == len(lora_linear.lora_a_stacked)
            == len(lora_linear.lora_b_stacked)
            == n_slices
        )

        return linear, lora_linear

    for i in range(NUM_RANDOM_SEEDS):
        set_random_seed(i)

        id_to_index = get_random_id_to_index(num_loras, max_loras)

        linear, lora_linear = create_column_parallel_packed_layer(i)
        assert torch.equal(linear.weight, lora_linear.weight)
        lora_linear.set_mapping(punica_wrapper)
        lora_dict, sublora_dict = populate_loras(
            id_to_index,
            layer=lora_linear,
            layer_weights=linear.weight,
            repeats=repeats,
        )

        inputs, index_mapping, prompt_mapping = create_random_inputs(
            active_lora_ids=list(lora_dict.keys()),
            num_inputs=32 * num_loras,
            input_size=(1, 4096),
            input_range=(0, 1),
            input_type=torch.float16,
            device=device,
        )
        lora_mapping = LoRAMapping(index_mapping, prompt_mapping, is_prefill=stage)

        punica_wrapper.update_metadata(
            lora_mapping,
            id_to_index,
            max_loras,
            512,
        )

        lora_result = lora_linear(torch.cat(inputs))[0]

        expected_results: list[torch.Tensor] = []
        for input_, lora_id in zip(inputs, prompt_mapping):
            result = linear(input_)[0]
            subloras = sublora_dict[lora_id]
            for i, sublora in enumerate(subloras):
                result[
                    :, sublora.lora_b.shape[0] * i : sublora.lora_b.shape[0] * (i + 1)
                ] += input_ @ sublora.lora_a.T @ sublora.lora_b.T * sublora.scaling
            expected_results.append(result)
        expected_result = torch.cat(expected_results)

        rtol, atol = TOLERANCES[lora_result.dtype]
        torch.testing.assert_close(lora_result, expected_result, rtol=rtol, atol=atol)

        for slot_idx in range(max_loras):
            lora_linear.reset_lora(slot_idx)

        inputs, index_mapping, prompt_mapping = create_random_inputs(
            active_lora_ids=[0],
            num_inputs=32 * num_loras,
            input_size=(1, 4096),
            input_range=(0, 1),
            input_type=torch.float16,
            device=device,
        )
        lora_mapping = LoRAMapping(index_mapping, prompt_mapping, is_prefill=stage)

        punica_wrapper.update_metadata(
            lora_mapping,
            id_to_index,
            max_loras,
            512,
        )

        lora_result = lora_linear(torch.cat(inputs))[0]
        expected_result = linear(torch.cat(inputs))[0]

        rtol, atol = TOLERANCES[lora_result.dtype]
        torch.testing.assert_close(lora_result, expected_result, rtol=rtol, atol=atol)