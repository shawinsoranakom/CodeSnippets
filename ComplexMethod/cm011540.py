def strategy(
        op: OpOverload,
        args_schema: ArgsType,
        kwargs_schema: KwargsType,
    ) -> list[list[Placement | _ShardingPlaceholder]]:
        tensor_arg_metas: list[TensorMeta] = [
            arg for arg in args_schema if isinstance(arg, TensorMeta)
        ]
        common_shape = torch.broadcast_shapes(
            *[arg.shape for arg in args_schema if isinstance(arg, TensorMeta)]
        )
        # For multi-output ops (e.g. frexp), all outputs share the same
        # pointwise sharding, so replicate the output placement.
        num_outputs = sum(1 for r in op._schema.returns if "Tensor" in str(r.type))
        placements: list[list[Placement | _ShardingPlaceholder]] = []
        for i in range(len(common_shape)):
            shard_placements: list[Placement | _ShardingPlaceholder] = [
                _ShardingPlaceholder(i)
            ] * num_outputs
            for arg in tensor_arg_metas:
                common_dim_to_arg_dim = infer_broadcast_dims_map(
                    common_shape, arg.shape
                )
                # If the output shard dim maps to an input dim, shard that
                # input dim; otherwise it was broadcast, so replicate.
                if common_dim_to_arg_dim[i] >= 0:
                    shard_placements.append(
                        _ShardingPlaceholder(common_dim_to_arg_dim[i])
                    )
                else:
                    shard_placements.append(Replicate())
            placements.append(shard_placements)
        if partial_extra_rules:
            n_tensors = len(tensor_arg_metas)
            expected_len = num_outputs + n_tensors
            for rule in partial_extra_rules:
                # Filter rather than assert: some ops (e.g. mul.Tensor) mix
                # unary rules (len 2, for scalar promotion) and binary rules
                # (len 3, for tensor-tensor), so mismatched lengths are expected.
                # see _MUL_RULES to see how _UNARY_LINEAR_RULES handles the
                # scalar promotion case
                if len(rule) == expected_len:
                    placements.append(rule)
        return placements