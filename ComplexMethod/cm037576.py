def weight_loader_v2(
        self,
        param: BasevLLMParameter,
        loaded_weight: torch.Tensor,
        loaded_shard_id: tuple[int, ...] | int | None = None,
    ):
        self.validate_shard_id(loaded_shard_id)
        if loaded_shard_id is None or isinstance(loaded_shard_id, tuple):
            if isinstance(param, PerTensorScaleParameter):
                if isinstance(loaded_shard_id, tuple):
                    for idx in loaded_shard_id:
                        param.load_merged_column_weight(
                            loaded_weight=loaded_weight, shard_id=idx
                        )
                else:
                    # When weights are already fused on disk (e.g. Phi-3's
                    # gate_up_proj), there is only a single scale for the
                    # entire fused matrix. Fill all slots with this scale
                    # to ensure that any subsequent reduction (like .max())
                    # works correctly while preserving the parameter shape.
                    for idx in range(param.data.shape[0]):
                        param.load_merged_column_weight(
                            loaded_weight=loaded_weight, shard_id=idx
                        )
                return
            elif type(param) in (RowvLLMParameter, BasevLLMParameter):
                param.load_merged_column_weight(loaded_weight=loaded_weight)
                return
            output_sizes = (
                [self.output_sizes[idx] for idx in loaded_shard_id]
                if loaded_shard_id
                else None
            )
            if isinstance(param, BlockQuantScaleParameter):
                weight_block_size = getattr(self, "weight_block_size", None)
                output_sizes = [
                    adjust_block_scale_shard(weight_block_size, size, 0)[0]
                    for size in (output_sizes or self.output_sizes)
                ]
            # TODO: @dsikka - move to parameter.py
            self._load_fused_module_from_checkpoint(
                param, loaded_weight, output_sizes=output_sizes
            )
            return

        assert loaded_shard_id < len(self.output_sizes)

        shard_offset = sum(self.output_sizes[:loaded_shard_id])
        shard_size = self.output_sizes[loaded_shard_id]
        shard_offset //= self.tp_size
        shard_size //= self.tp_size

        if isinstance(param, BlockQuantScaleParameter):
            weight_block_size = getattr(self, "weight_block_size", None)
            shard_size, shard_offset = adjust_block_scale_shard(
                weight_block_size, shard_size, shard_offset
            )

        param.load_merged_column_weight(
            loaded_weight=loaded_weight,
            shard_id=loaded_shard_id,
            shard_offset=shard_offset,
            shard_size=shard_size,
            tp_rank=self.tp_rank,
        )