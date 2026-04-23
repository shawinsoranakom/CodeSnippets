def test_expand_matmul_like_strategy_to_3d_mesh(self):
        """Test expanding matmul-like single-dim strategies to a 3D mesh.

        This test verifies that:
        1. Single-dim matmul strategies (S0,R -> S0 and R,S1->S1) are correctly expanded to 3D
        2. The implicit full-replication rule is included
        3. _ShardingPlaceholder is correctly replaced with actual Shard placements
        4. tensor_meta is properly populated for output and input specs
        """
        mesh = DeviceMesh("cpu", mesh=torch.arange(8).reshape(2, 2, 2))
        M, K, N = 64, 32, 64
        left_meta, right_meta = _get_mm_metas(M, K, N)

        # Compute expected output tensor_meta for matmul: (M, K) @ (K, N) -> (M, N)
        output_meta = TensorMeta(
            shape=torch.Size([M, N]),
            stride=(N, 1),
            dtype=torch.float32,
        )

        # Create DTensorSpec for inputs with Shard placements using helper
        # Left input sharded on dim 0 across first mesh dim, replicated on others
        # Right input replicated across all mesh dims
        left_spec, right_spec = _get_mm_specs(
            mesh,
            left_meta,
            right_meta,
            left_placements=(Shard(0), Replicate(), Replicate()),
            right_placements=(Replicate(), Replicate(), Replicate()),
        )

        # Create OpSchema
        op_schema = OpSchema(
            op=torch.ops.aten.mm.default,
            args_schema=(
                OpStrategy([OpSpec(left_spec)]),
                OpStrategy([OpSpec(right_spec)]),
            ),
            kwargs_schema={},
        )

        # Expand the strategy to the full mesh
        expanded_strategy_fn = _expand_single_dim_strategy_to_mesh(
            mesh, op_schema, _SingleDimStrategyInfo(mm_single_dim_strategy), output_meta
        )
        strategy = expanded_strategy_fn(
            torch.ops.aten.matmul.default, op_schema.args_meta, op_schema.kwargs_meta
        )
        self.assertIsInstance(strategy, OpStrategy)

        # For a 3D mesh with 8 single-dim strategies per mesh dim
        # (3 sharding + 4 per-input linearity + 1 implicit replicate),
        # we get 8^3 = 512 strategy combinations.
        self.assertEqual(len(strategy.strategies), 512)

        all_replicate_found = False
        shard_0_found = False
        for op_spec in strategy.strategies:
            output_spec = op_spec.output_spec
            input_specs = op_spec.input_specs
            self.assertIsNotNone(input_specs)

            # Verify tensor_meta is populated for output spec
            self.assertIsNotNone(
                output_spec.tensor_meta, "Output spec should have tensor_meta populated"
            )
            self.assertEqual(output_spec.tensor_meta.shape, torch.Size([M, N]))
            self.assertEqual(output_spec.tensor_meta.dtype, torch.float32)

            # Verify tensor_meta is populated for input specs
            self.assertIsNotNone(
                input_specs[0].tensor_meta,
                "Left input spec should have tensor_meta populated",
            )
            self.assertEqual(input_specs[0].tensor_meta.shape, torch.Size([M, K]))
            self.assertEqual(input_specs[0].tensor_meta.dtype, torch.float32)

            self.assertIsNotNone(
                input_specs[1].tensor_meta,
                "Right input spec should have tensor_meta populated",
            )
            self.assertEqual(input_specs[1].tensor_meta.shape, torch.Size([K, N]))
            self.assertEqual(input_specs[1].tensor_meta.dtype, torch.float32)

            # Check if this is the all-replicate strategy
            if (
                all(isinstance(p, Replicate) for p in output_spec.placements)
                and all(isinstance(p, Replicate) for p in input_specs[0].placements)
                and all(isinstance(p, Replicate) for p in input_specs[1].placements)
            ):
                all_replicate_found = True

            # Placeholders should have been filled
            self.assertFalse(
                any(isinstance(p, _ShardingPlaceholder) for p in output_spec.placements)
            )
            for input_spec in input_specs:
                self.assertFalse(
                    any(
                        isinstance(p, _ShardingPlaceholder)
                        for p in input_spec.placements
                    )
                )
            if any(
                isinstance(p, Shard) and p.dim == 0 for p in input_specs[0].placements
            ):
                shard_0_found = True

        self.assertTrue(
            all_replicate_found,
            "Implicit full-replication rule not found in expanded strategies",
        )
        # Verify at least one strategy has Shard(0) placement for left input
        self.assertTrue(
            shard_0_found,
            "No strategy found with Shard(0) for left input",
        )