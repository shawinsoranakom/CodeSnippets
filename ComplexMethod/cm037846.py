def _unquantized_generator(
        self, hf_weights_files, use_safetensors, quant_state_dict
    ) -> Generator:
        from bitsandbytes.functional import quantize_4bit

        global_tp_size = get_tensor_model_parallel_world_size()
        global_tp_rank = get_tensor_model_parallel_rank()
        check_match = (
            lambda weight_name, module_name: weight_name.removesuffix(".weight")
            == module_name
        )
        for (
            org_weight_name,
            mapped_weight_name,
            weight_tensor,
        ) in self._hf_weight_iter(hf_weights_files, use_safetensors):
            # override tp_size and tp_rank if the module has disabled TP
            if any(
                tp_disabled_module in mapped_weight_name
                for tp_disabled_module in self.tp_disabled_modules
            ):
                tp_size = 1
                tp_rank = 0
            else:
                tp_size = global_tp_size
                tp_rank = global_tp_rank

            if any(
                target_module in mapped_weight_name
                for target_module in self.target_modules
            ) and mapped_weight_name.endswith(".weight"):
                # Without sharding
                if any(
                    check_match(mapped_weight_name, module)
                    for module in self.unsharded_weights_modules
                ):
                    weight_sub_tensor = weight_tensor
                # Shard by column
                elif any(
                    check_match(mapped_weight_name, module)
                    for module in self.column_sharded_weights_modules
                ):
                    total_size = weight_tensor.size(-1)
                    start_index = total_size // tp_size * tp_rank
                    end_index = total_size // tp_size * (tp_rank + 1)
                    weight_sub_tensor = weight_tensor[..., start_index:end_index]
                # Weights have fused on disk. In this case, we assume that the
                # weight and module use same name.
                elif any(
                    check_match(mapped_weight_name, module)
                    for module in self.maybe_fused_weights_modules
                ):
                    # special case for fused weights
                    # get the size of each shard weight tensor
                    total_shard_sizes = next(
                        (
                            sizes
                            for module, sizes in self.maybe_fused_weights_modules.items()  # noqa: E501
                            if check_match(mapped_weight_name, module)
                        )
                    )
                    total_size = weight_tensor.size(0)
                    assert total_size == sum(total_shard_sizes)
                    # get the start/end index of each shard weight tensor
                    total_start_index = list(
                        itertools.accumulate([0] + total_shard_sizes)
                    )[:-1]
                    shard_weights_index = [
                        (
                            idx + size // tp_size * tp_rank,
                            idx + size // tp_size * (tp_rank + 1),
                        )
                        for idx, size in zip(total_start_index, total_shard_sizes)
                    ]
                    # slice and reorder the weight tensor
                    weight_tensor = [
                        weight_tensor[start_index:end_index, ...]
                        for start_index, end_index in shard_weights_index
                    ]
                    weight_sub_tensor = torch.cat(weight_tensor, dim=0)
                # Shard by row
                else:
                    total_size = weight_tensor.size(0)
                    start_index = total_size // tp_size * tp_rank
                    end_index = total_size // tp_size * (tp_rank + 1)
                    weight_sub_tensor = weight_tensor[start_index:end_index, ...]

                # bitsandbytes requires data in GPU
                if weight_sub_tensor.is_cuda:
                    loaded_weight = weight_sub_tensor
                else:
                    loaded_weight = weight_sub_tensor.to(
                        device=current_platform.device_type
                    )

                # remove the following after the issue is fixed:
                # https://github.com/bitsandbytes-foundation/bitsandbytes/issues/1342
                if loaded_weight.is_contiguous() is False:
                    loaded_weight = loaded_weight.contiguous()

                with set_default_torch_dtype(torch.float32):
                    processed_weight, quant_state = quantize_4bit(
                        loaded_weight,
                        compress_statistics=True,
                        quant_type="nf4",
                    )

                quant_state_dict[mapped_weight_name] = quant_state
            else:
                processed_weight = weight_tensor
            yield org_weight_name, processed_weight