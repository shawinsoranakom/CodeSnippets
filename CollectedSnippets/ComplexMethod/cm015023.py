def test_reduction_ops_reduce(self, device, op):
        """Test that operators with reduction tag actually reduce numel when dim is specified."""
        samples = op.sample_inputs(device, torch.float32)

        for sample in samples:
            if "dim" not in sample.kwargs:
                continue

            dim_val = sample.kwargs["dim"]

            # Call the operation
            result = op(sample.input, *sample.args, **sample.kwargs)

            if isinstance(result, torch.Tensor):
                if dim_val is None:
                    dim_val = list(range(sample.input.ndim))
                reduction_dims = [dim_val] if isinstance(dim_val, int) else dim_val

                # Skip 0 dim for now
                if any(abs(dim) >= sample.input.ndim for dim in reduction_dims):
                    continue

                reduction_factor = 1
                for dim in reduction_dims:
                    reduction_factor *= sample.input.shape[dim]

                expected_numel = sample.input.numel() // reduction_factor

                self.assertEqual(
                    result.numel(),
                    expected_numel,
                    f"{op.name} with dim={dim_val} should reduce numel by factor of {reduction_factor} "
                    f"(input: {sample.input.numel()}, expected: {expected_numel}, got: {result.numel()})",
                )