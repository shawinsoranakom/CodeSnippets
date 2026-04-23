def test_expand_filters_mixed_partial_types(self):
        """Test that expand_to_full_mesh_op_strategy filters out mixed partial types.

        When single-dim strategies are expanded to a multi-dimensional mesh, some
        combinations could create specs with mixed Partial reduce types (e.g.,
        Partial("sum") and Partial("max") in the same placement list). These
        combinations should be filtered out since mixed partial types don't commute.

        The exception is sum+avg which DO commute and should be allowed.
        """
        mesh = DeviceMesh("cpu", mesh=torch.arange(4).reshape(2, 2))
        meta = TensorMeta(torch.Size([8, 8]), (8, 1), torch.float32)

        # Create input spec with Replicate placement
        input_spec = DTensorSpec(mesh, (Replicate(), Replicate()), meta)

        # Create OpSchema
        op_schema = OpSchema(
            op=torch.ops.aten.mul.Tensor,
            args_schema=(
                OpStrategy([OpSpec(input_spec)]),
                OpStrategy([OpSpec(input_spec)]),
            ),
            kwargs_schema={},
        )

        # Define strategies that would create mixed partials when expanded:
        # - Strategy 1: Partial("sum") for all tensors
        # - Strategy 2: Partial("max") for all tensors
        # When expanded to 2D mesh, combinations like (P_sum, P_max) should be filtered
        single_mesh_dim_strategies = [
            [Partial("sum"), Partial("sum"), Partial("sum")],
            [Partial("max"), Partial("max"), Partial("max")],
            [Replicate(), Replicate(), Replicate()],
        ]

        result = expand_to_full_mesh_op_strategy(
            mesh,
            op_schema,
            single_mesh_dim_strategies,
            output_tensor_meta=meta,
        )

        # Verify no strategy has mixed partial types (except sum+avg)
        for strategy in result.strategies:
            output_spec = strategy.output_spec
            partial_reduce_ops = {
                p.reduce_op for p in output_spec.placements if isinstance(p, Partial)
            }
            # Either 0 or 1 partial type, or exactly {"sum", "avg"}
            if len(partial_reduce_ops) > 1:
                self.assertEqual(
                    partial_reduce_ops,
                    {"sum", "avg"},
                    f"Found invalid mixed partials: {partial_reduce_ops}",
                )

        # Verify that homogeneous partial strategies ARE included
        # (P_sum, P_sum) and (P_max, P_max) should be valid
        found_all_sum = False
        found_all_max = False
        for strategy in result.strategies:
            output_spec = strategy.output_spec
            if all(
                isinstance(p, Partial) and p.reduce_op == "sum"
                for p in output_spec.placements
            ):
                found_all_sum = True
            if all(
                isinstance(p, Partial) and p.reduce_op == "max"
                for p in output_spec.placements
            ):
                found_all_max = True

        self.assertTrue(found_all_sum, "Should include (P_sum, P_sum) strategy")
        self.assertTrue(found_all_max, "Should include (P_max, P_max) strategy")