def test_unsupported_expand_weights(self, device, dtype, op):
        sample_inputs = op.sample_inputs(device, dtype, requires_grad=True)
        unsupported_inputs = supported_inputs(op, sample_inputs, supported_inputs=False)
        for sample_input in unsupported_inputs:
            with self.assertRaisesRegex(RuntimeError, r"Expanded Weights"):
                if (
                    op.name == "nn.functional.embedding"
                ):  # embedding flips its argument order for autograd tests
                    sample_input = SampleInput(
                        sample_input.args[0],
                        args=(sample_input.input,),
                        kwargs=sample_input.kwargs,
                    )
                input = sample_input.input

                batch_size = input.shape[0] if len(input.shape) > 1 else 1

                # get per sample grads with ExpandedWeights objects
                (ew_input, ew_args, ew_kwargs) = make_expanded_weight(
                    sample_input, batch_size
                )
                result = run_op(op, ew_input, *ew_args, **ew_kwargs)
                diff_input_list = (
                    (ew_input,) + tuple(ew_args) + tuple(ew_kwargs.values())
                )
                diff_input_list = [i for i in diff_input_list if is_diff_tensor(i)]
                diff_input_list = [
                    i.orig_weight if isinstance(i, ExpandedWeight) else i
                    for i in diff_input_list
                ]
                result.sum().backward()