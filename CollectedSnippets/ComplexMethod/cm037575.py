def weight_loader(
        self,
        param: Parameter,
        loaded_weight: torch.Tensor,
        loaded_shard_id: tuple[int, ...] | int | None = None,
    ):
        self.validate_shard_id(loaded_shard_id)
        # Special case for GGUF
        # initialize GGUF param after we know the quantize type
        is_gguf_weight = getattr(param, "is_gguf_weight", False)
        is_gguf_weight_type = getattr(param, "is_gguf_weight_type", False)
        if isinstance(loaded_shard_id, tuple) and (
            is_gguf_weight or is_gguf_weight_type
        ):
            raise NotImplementedError(
                "Shard id with multiple indices is not supported for GGUF."
            )
        if is_gguf_weight_type:
            if loaded_shard_id is not None:
                param.data[loaded_shard_id].copy_(loaded_weight)
                param.shard_weight_type[loaded_shard_id] = loaded_weight.item()
            else:
                param.shard_weight_type = {
                    i: loaded_weight.item() for i, _ in enumerate(self.output_sizes)
                }
            return

        if is_gguf_weight:
            output_dim = getattr(param, "output_dim", None)
            shard_size = loaded_weight.size(output_dim) // self.tp_size
            start_idx = self.tp_rank * shard_size

            if loaded_shard_id is not None:
                loaded_weight = loaded_weight.narrow(output_dim, start_idx, shard_size)
                param.shard_id.append(loaded_shard_id)
                param.shard_id_map[loaded_shard_id] = len(param.data_container)
                param.data_container.append(loaded_weight)
                return

        param_data = param.data
        output_dim = getattr(param, "output_dim", None)
        # Special case for per-tensor scale to load scalar into fused array.
        needs_scalar_to_array = getattr(param, "needs_scalar_to_array", False)

        if loaded_shard_id is None or isinstance(loaded_shard_id, tuple):
            # Loaded weight is already fused on disk (mlp).
            # (e.g., Phi-3's gate_up_proj).
            if output_dim is None:
                if needs_scalar_to_array:
                    param_data, loaded_weight = adjust_scalar_to_fused_array(
                        param_data, loaded_weight, 0
                    )

                assert param_data.shape == loaded_weight.shape
                param_data.copy_(loaded_weight)
                return

            output_sizes = (
                self.output_sizes[loaded_shard_id[0] : loaded_shard_id[-1] + 1]
                if loaded_shard_id is not None
                else self.output_sizes
            )
            current_shard_offset = 0
            use_bitsandbytes_4bit = getattr(param, "use_bitsandbytes_4bit", False)
            if (
                use_bitsandbytes_4bit
                and isinstance(loaded_shard_id, tuple)
                and self.tp_size > 1
            ):
                raise NotImplementedError(
                    "Shard id with multiple indices is not supported "
                    "for BNB quantization with TP yet."
                )
            shard_offsets: list[tuple[int, int, int]] = []
            for i, output_size in enumerate(output_sizes):
                shard_offsets.append((i, current_shard_offset, output_size))
                current_shard_offset += output_size
            packed_dim = getattr(param, "packed_dim", None)
            for shard_id, shard_offset, shard_size in shard_offsets:
                # Special case for Quantization.
                # If quantized, we need to adjust the offset and size to account
                # for the packing.
                # Add check to adjust the size/offset for FP8 block scales
                if isinstance(param, BlockQuantScaleParameter):
                    weight_block_size = getattr(self, "weight_block_size", None)
                    shard_size, shard_offset = adjust_block_scale_shard(
                        weight_block_size, shard_size, shard_offset
                    )

                if packed_dim == output_dim:
                    shard_size = shard_size // param.packed_factor
                    shard_offset = shard_offset // param.packed_factor
                    # Special case for Marlin.
                    shard_size, shard_offset = adjust_marlin_shard(
                        param, shard_size, shard_offset
                    )

                if use_bitsandbytes_4bit:
                    index = list(itertools.accumulate([0] + self.output_sizes))
                    orig_offsets = {
                        str(i): (index[i], size)
                        for i, size in enumerate(self.output_sizes)
                    }
                    orig_offsets["total"] = (self.output_size, 0)
                    shard_size, shard_offset = adjust_bitsandbytes_4bit_shard(
                        param, orig_offsets, str(shard_id)
                    )

                loaded_weight_shard = loaded_weight.narrow(
                    output_dim, shard_offset, shard_size
                )
                self.weight_loader(param, loaded_weight_shard, shard_id)
            return

        assert loaded_shard_id < len(self.output_sizes)
        if output_dim is not None:
            shard_offset = sum(self.output_sizes[:loaded_shard_id])
            shard_size = self.output_sizes[loaded_shard_id]
            shard_offset //= self.tp_size
            shard_size //= self.tp_size

            if isinstance(param, BlockQuantScaleParameter):
                weight_block_size = getattr(self, "weight_block_size", None)
                shard_size, shard_offset = adjust_block_scale_shard(
                    weight_block_size, shard_size, shard_offset
                )

            # Special case for quantization.
            # If quantized, we need to adjust the offset and size to account
            # for the packing.
            packed_dim = getattr(param, "packed_dim", None)
            if packed_dim == output_dim:
                shard_size = shard_size // param.packed_factor
                shard_offset = shard_offset // param.packed_factor
                # Special case for Marlin.
                shard_size, shard_offset = adjust_marlin_shard(
                    param, shard_size, shard_offset
                )

            use_bitsandbytes_4bit = getattr(param, "use_bitsandbytes_4bit", False)
            is_sharded_weight = getattr(param, "is_sharded_weight", False)
            # bitsandbytes loads the weights of the specific portion
            # no need to narrow
            is_sharded_weight = is_sharded_weight or use_bitsandbytes_4bit

            if use_bitsandbytes_4bit:
                index = list(itertools.accumulate([0] + self.output_sizes))
                orig_offsets = {
                    str(i): (index[i], size) for i, size in enumerate(self.output_sizes)
                }
                orig_offsets["total"] = (self.output_size, 0)
                shard_size, shard_offset = adjust_bitsandbytes_4bit_shard(
                    param, orig_offsets, str(loaded_shard_id)
                )
            param_data = param_data.narrow(output_dim, shard_offset, shard_size)
            start_idx = self.tp_rank * shard_size
            if not is_sharded_weight:
                loaded_weight = loaded_weight.narrow(output_dim, start_idx, shard_size)
        # Special case for per-tensor scales in fused case.
        elif needs_scalar_to_array:
            param_data, loaded_weight = adjust_scalar_to_fused_array(
                param_data, loaded_weight, loaded_shard_id
            )

        else:
            ignore_warning = getattr(param, "ignore_warning", False)
            if not ignore_warning:
                logger.warning(
                    "Loading a weight without `output_dim` attribute in "
                    "MergedColumnParallelLinear, assume the weight is "
                    "the same for all partitions."
                )

        assert param_data.shape == loaded_weight.shape
        param_data.copy_(loaded_weight)