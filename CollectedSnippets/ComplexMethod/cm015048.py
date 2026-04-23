def test_sparse_csr_unary_inplace(self, device, dtype, op):
        samples = op.sample_inputs(device, dtype)

        if op.inplace_variant is None:
            self.skipTest("Skipped! Inplace variant not supported!")

        for sample in samples:
            if not torch.is_tensor(sample.input):
                raise AssertionError(f"expected tensor, got {type(sample.input)}")
            # Sparse CSR only supports 2D tensors as inputs
            # Fail early to prevent silent success with this test
            if sample.input.ndim != 2:
                raise ValueError(f"Expected 2D tensor but got tensor with dimension: {sample.input.ndim}.")

            sample.input = sample.input.to_sparse_csr()
            expect = op(sample.input, *sample.args, **sample.kwargs)

            if not torch.can_cast(expect.dtype, dtype):
                with self.assertRaisesRegex(RuntimeError, "result type"):
                    op.inplace_variant(sample.input, *sample.args, **sample.kwargs)
                continue

            if sample.input.is_complex() and op.name == "abs":
                with self.assertRaisesRegex(RuntimeError, "not supported"):
                    op.inplace_variant(sample.input, *sample.args, **sample.kwargs)
                continue

            actual = op.inplace_variant(sample.input, *sample.args, **sample.kwargs)

            self.assertIs(actual, sample.input)
            self.assertEqual(actual, expect)