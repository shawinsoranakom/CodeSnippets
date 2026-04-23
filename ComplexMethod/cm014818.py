def test_expanded_weight_forward(self, device, dtype, op):
        sample_inputs = op.sample_inputs(device, dtype)
        for sample_input in supported_inputs(op, sample_inputs):
            if (
                op.name == "nn.functional.embedding"
            ):  # embedding flips its argument order for autograd tests
                sample_input = SampleInput(
                    sample_input.args[0].clone(),
                    args=(sample_input.input.clone(),),
                    kwargs=sample_input.kwargs,
                )
                if (
                    "cuda" in device
                    and "max_norm" in sample_input.kwargs
                    and "padding_idx" in sample_input.kwargs
                ):
                    self.skipTest(
                        "embedding is non-determinstic in this case, see issue #74679"
                    )
            batch_size = (
                sample_input.input.shape[0] if len(sample_input.input.shape) > 1 else 1
            )
            for loss_reduction in ["sum", "mean"]:
                (ew_input, ew_args, ew_kwargs) = make_expanded_weight(
                    sample_input, batch_size, loss_reduction
                )
                expanded_weight_result = run_op(op, ew_input, *ew_args, **ew_kwargs)
                normal_result = run_op(
                    op, sample_input.input, *sample_input.args, **sample_input.kwargs
                )
                self.assertEqual(expanded_weight_result, normal_result)