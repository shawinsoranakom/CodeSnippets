def test_dynamic_shape_mm(self, device, dtype):
        # Test that the mm decomp does not evaluate expressions for dynamic shapes

        shape_env = ShapeEnv()
        fake_mode = FakeTensorMode(shape_env=shape_env)

        # Only test decomp for cpu to match fake tensors from dynamo
        if device != "cpu":
            return

        for t_size in ts_list:
            ((a1_0, a1_1, a2_0, a2_1)) = t_size

            # Create the fake tensors
            t1 = create_fake_tensor_with_dynamic_size(
                rand_math_tensor((a1_0, a1_1), dtype=dtype, device=device),
                fake_mode,
            )
            t2 = create_fake_tensor_with_dynamic_size(
                rand_math_tensor((a2_0, a2_1), dtype=dtype, device=device),
                fake_mode,
            )

            # Save the expression types to check if any symints are evaluated
            og_t1_expr_types = [
                type(d.node.expr) if type(d) is torch.SymInt else int for d in t1.size()
            ]
            og_t2_expr_types = [
                type(d.node.expr) if type(d) is torch.SymInt else int for d in t2.size()
            ]

            r = mm(t1, t2)

            # Make sure all symints are not evaluated
            new_t1_expr_types = [
                type(d.node.expr) if type(d) is torch.SymInt else int for d in t1.size()
            ]
            new_t2_expr_types = [
                type(d.node.expr) if type(d) is torch.SymInt else int for d in t2.size()
            ]
            self.assertTrue(
                all(
                    og_t1_expr_types[i] == new_t1_expr_types[i]
                    for i in range(len(og_t1_expr_types))
                )
            )
            self.assertTrue(
                all(
                    og_t2_expr_types[i] == new_t2_expr_types[i]
                    for i in range(len(og_t2_expr_types))
                )
            )

            if r is not NotImplemented:
                # Check that the output is well formed
                self.assertEqual(t1.size(0), r.size(0))
                self.assertEqual(t2.size(1), r.size(1))
                r_expr_types = [
                    type(d.node.expr) if type(d) is torch.SymInt else int
                    for d in r.size()
                ]
                self.assertTrue(r_expr_types[0] == og_t1_expr_types[0])
                self.assertTrue(r_expr_types[1] == og_t2_expr_types[1])