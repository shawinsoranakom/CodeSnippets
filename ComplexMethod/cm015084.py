def test_addcmul_alpha_one_fma_parity(self, device, dtype):
        # Test that addcmul with alpha=1 produces bitwise identical results
        # to add with alpha=scalar_val (when tensor1 is a 0D tensor with that value).
        # This verifies that the alpha=1 special case uses FMA correctly.
        #
        # The computation is: input + 1 * tensor1 * tensor2
        # When alpha=1, this should match: input + tensor1 * tensor2
        # And when tensor1 is a 0D tensor with value scalar_val, this should match:
        # input.add(tensor2, alpha=scalar_val)
        N = 5

        # Test with various scalar values for tensor1
        for scalar_val in [1.0, 2.0, 0.5, -1.0, 3.14159]:
            # Create tensors - use same seed for reproducibility
            inputs = [
                make_tensor((10, 10), dtype=dtype, device=device) for _ in range(N)
            ]
            tensor2s = [
                make_tensor((10, 10), dtype=dtype, device=device) for _ in range(N)
            ]

            # Create 0D tensors (scalars on GPU) for tensor1
            tensor1s_0d = [
                torch.tensor(scalar_val, dtype=dtype, device=device) for _ in range(N)
            ]

            # 1. Regular addcmul with alpha=1
            regular_addcmul_results = [
                torch.addcmul(inp, t1, t2, value=1.0)
                for inp, t1, t2 in zip(inputs, tensor1s_0d, tensor2s)
            ]

            # 2. foreach_addcmul with alpha=1
            foreach_addcmul_results = torch._foreach_addcmul(
                inputs, tensor1s_0d, tensor2s, value=1.0
            )

            # 3. add with alpha=tensor1.item() - this is what FMA should match
            # input + scalar_val * tensor2
            # We use t1.item() to get the actual float32 value stored in the tensor,
            # not the Python float64 scalar_val which may differ due to precision
            add_alpha_results = [
                inp.add(t2, alpha=t1.item())
                for inp, t1, t2 in zip(inputs, tensor1s_0d, tensor2s)
            ]

            inp, t1, t2 = inputs[0], tensor1s_0d[0], tensor2s[0]

            # Verify bitwise equality between regular addcmul and foreach_addcmul
            self.assertEqual(
                regular_addcmul_results,
                foreach_addcmul_results,
                atol=0,
                rtol=0,
            )

            # Verify bitwise equality between addcmul (alpha=1) and add (alpha=scalar_val)
            # This tests that the FMA optimization produces correct results
            self.assertEqual(
                regular_addcmul_results,
                add_alpha_results,
                atol=0,
                rtol=0,
            )

        # Also test with non-0D tensor1 to ensure the regular path still works
        inputs = [make_tensor((10, 10), dtype=dtype, device=device) for _ in range(N)]
        tensor1s = [make_tensor((10, 10), dtype=dtype, device=device) for _ in range(N)]
        tensor2s = [make_tensor((10, 10), dtype=dtype, device=device) for _ in range(N)]

        regular_results = [
            torch.addcmul(inp, t1, t2, value=1.0)
            for inp, t1, t2 in zip(inputs, tensor1s, tensor2s)
        ]
        foreach_results = torch._foreach_addcmul(inputs, tensor1s, tensor2s, value=1.0)

        self.assertEqual(
            regular_results,
            foreach_results,
            atol=0,
            rtol=0,
        )