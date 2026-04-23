def test_layer_norm_backward(self, output_mask):
        from torch.testing._internal.common_methods_invocations import sample_inputs_layer_norm

        device = "meta"
        dtype = torch.float32

        samples = sample_inputs_layer_norm(None, device, dtype, requires_grad=False)

        for sample in samples:
            with self.subTest(sample=sample):
                # handle optional weight and bias
                if len(sample.args) != 3:
                    sample.args = (*sample.args, *([None] * (3 - len(sample.args))))

                grad_out = torch.ones_like(sample.input)
                normalized_shape, weight, bias = sample.args
                ndims_after_reduction = sample.input.ndim - len(normalized_shape)
                mean_shape = grad_out.shape[:ndims_after_reduction]
                mean = torch.zeros(mean_shape, device=device, dtype=dtype)
                rstd = torch.zeros(mean_shape, device=device, dtype=dtype)

                expected_shapes = (
                    sample.input.shape if output_mask[0] else None,
                    weight.shape if output_mask[1] and weight is not None else None,
                    bias.shape if output_mask[2] and bias is not None else None)

                args = [grad_out, sample.input, normalized_shape, mean, rstd, weight, bias]

                self._norm_backwards_test_helper(torch.ops.aten.native_layer_norm_backward,
                                                 args, output_mask, expected_shapes)