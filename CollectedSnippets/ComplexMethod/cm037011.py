def test_merged_column_parallel_variable_slice(
    default_vllm_config, dist_init, num_loras, num_slices, device, stage
) -> None:
    if current_platform.is_cuda_alike():
        torch.accelerator.set_device_index(device)

    max_loras = 8
    torch.set_default_device(device)
    lora_config = LoRAConfig(
        max_loras=max_loras, max_lora_rank=8, lora_dtype=torch.float16
    )
    punica_wrapper = get_punica_wrapper(8192, 256, device, lora_config=lora_config)

    # Set number of output slices
    output_sizes = [1024 + i * 256 for i in range(num_slices)]
    total_output = sum(output_sizes)

    def create_layer(idx: int = 0):
        # Create linear layer
        linear = MergedColumnParallelLinear(
            4096,
            output_sizes,
            bias=False,
            params_dtype=torch.float16,
            prefix=f"layer_{idx}",
        )
        linear.weight.data = torch.rand_like(linear.weight.data)

        # Create linear layer with LoRA adapter
        lora_linear = MergedColumnParallelLinearVariableSliceWithLoRA(linear)
        lora_linear.create_lora_weights(max_loras, lora_config)
        return linear, lora_linear

    for i in range(NUM_RANDOM_SEEDS):
        set_random_seed(i)
        id_to_index = get_random_id_to_index(num_loras, max_loras)
        linear, lora_linear = create_layer(i)
        lora_linear.set_mapping(punica_wrapper)

        # Populate LoRA weights
        lora_dict, sublora_dict = {}, {}
        for slot_idx, lora_id in enumerate(id_to_index):
            if lora_id is not None:
                # Create random LoRA weights
                lora_a = torch.rand(8, 4096, dtype=torch.float16, device=device)
                lora_b = torch.rand(total_output, 8, dtype=torch.float16, device=device)
                lora_linear.set_lora(slot_idx, lora_a, lora_b)
                lora_dict[lora_id] = (lora_a, lora_b)

                # Split lora_b for expected computation
                sublora_dict[lora_id] = torch.split(lora_b, output_sizes, dim=0)

        inputs, index_mapping, prompt_mapping = create_random_inputs(
            active_lora_ids=list(lora_dict.keys()),
            num_inputs=32 * num_loras,
            input_size=(1, 4096),
            input_range=(0, 1),
            input_type=torch.float16,
            device=device,
        )
        lora_mapping = LoRAMapping(index_mapping, prompt_mapping, is_prefill=stage)
        punica_wrapper.update_metadata(lora_mapping, id_to_index, max_loras, 512)

        # Compute LoRA result
        lora_result = lora_linear(torch.cat(inputs))[0]

        # Compute expected result
        expected_results = []
        for input_, lora_id in zip(inputs, prompt_mapping):
            result = linear(input_)[0]
            lora_a, _ = lora_dict[lora_id]
            offset = 0
            # Compute expected result for each sublora
            for lora_b_slice in sublora_dict[lora_id]:
                sz = lora_b_slice.shape[0]
                result[:, offset : offset + sz] += input_ @ lora_a.T @ lora_b_slice.T
                offset += sz
            expected_results.append(result)

        # Check that the LoRA result is close to the expected result
        rtol, atol = TOLERANCES[lora_result.dtype]
        torch.testing.assert_close(
            lora_result, torch.cat(expected_results), rtol=rtol, atol=atol
        )

        # Reset LoRA weights and check results with zero LoRA weights
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
        punica_wrapper.update_metadata(lora_mapping, id_to_index, max_loras, 512)

        # After resetting LoRA weights,
        # lora_linear should behave like the base linear layer
        lora_result = lora_linear(torch.cat(inputs))[0]
        expected_result = linear(torch.cat(inputs))[0]

        rtol, atol = TOLERANCES[lora_result.dtype]
        torch.testing.assert_close(lora_result, expected_result, rtol=rtol, atol=atol)