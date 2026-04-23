def test_single_dim_strategy(self, dtype, op):
        torch.manual_seed(42)
        mesh = init_device_mesh(DEVICE_TYPE, (self.world_size,))
        sharding_prop = DTensor._op_dispatcher.sharding_propagator

        try:
            samples = list(op.sample_inputs(DEVICE_TYPE, dtype, requires_grad=False))
        except Exception:
            self.skipTest(f"Failed to get sample inputs for {op.name}")
        if not samples:
            self.skipTest(f"No sample inputs for {op.name}")

        sample = samples[0]
        args = (sample.input,) + tuple(sample.args)

        # create Replicated DTensors
        try:
            dtensor_args, dtensor_kwargs = pytree.tree_map_only(
                torch.Tensor,
                lambda t: distribute_tensor(t, mesh, (Replicate(),)),
                (args, sample.kwargs),
            )
        except Exception:
            self.skipTest(f"Failed to create replicate DTensors for {op.name}")

        # extract aten op/args/kwargs
        aten_op, aten_args, aten_kwargs = self._extract_aten_op_and_args(
            op.op, dtensor_args, dtensor_kwargs
        )

        single_dim_strats = sharding_prop.op_single_dim_strategy_funcs
        if aten_op not in single_dim_strats:
            self.skipTest(f"No single-dim strategy for {op.name}: {aten_op}")

        # extract tensor_meta, full tensors
        all_tensor_meta = []

        def _collect_tensor_meta(dt):
            meta = dt._spec.tensor_meta
            all_tensor_meta.append(meta)
            return meta

        args_meta, kwargs_meta = pytree.tree_map_only(
            DTensor, _collect_tensor_meta, (aten_args, aten_kwargs)
        )
        full_args, full_kwargs = pytree.tree_map_only(
            torch.Tensor, lambda t: t.full_tensor(), (aten_args, aten_kwargs)
        )

        # enumerate strategies, replace placeholders with Shard
        strategies = pytree.tree_map_only(
            _ShardingPlaceholder,
            lambda s: Shard(s.dim),
            single_dim_strats[aten_op](aten_op, args_meta, kwargs_meta),
        )
        n_inputs = len(all_tensor_meta)
        for strategy in strategies:
            input_placements = strategy[-n_inputs:]
            output_placements = strategy[:-n_inputs]

            # skip strategies with invalid shards
            def is_invalid_shard(meta, p):
                ndim = len(meta.shape)
                if (
                    not isinstance(p, Shard)
                    or ndim == 0
                    or p.dim >= ndim
                    or meta.shape[p.dim] == 0
                    or meta.shape[p.dim] % self.world_size != 0
                ):
                    return True
                return False

            if any(
                is_invalid_shard(t, p)
                for t, p in zip(all_tensor_meta, input_placements)
            ):
                continue

            self.assertTrue(
                validate_sharding_rule_sample(
                    aten_op,
                    full_args,
                    full_kwargs,
                    input_placements,
                    tuple(output_placements),
                    mesh,
                ),
                f"{op.name}: {input_placements} -> {tuple(output_placements)} failed",
            )