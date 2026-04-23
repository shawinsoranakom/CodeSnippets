def _test_consistency_helper(samples, variants):
            for sample in samples:
                # TODO: Check grad for all Tensors requiring grad if sample.input is TensorList
                tensor = (
                    sample.input
                    if isinstance(sample.input, torch.Tensor)
                    else sample.input[0]
                )

                # Computes function forward and backward values
                tensor.grad = None
                expected_forward = op(sample.input, *sample.args, **sample.kwargs)
                expected_grad = None

                output_process_fn_grad = (
                    sample.output_process_fn_grad
                    if sample.output_process_fn_grad
                    else lambda x: x
                )

                # Skips inplace variants if the output dtype is not the same as
                #   the input dtype
                skip_inplace = False
                if (
                    isinstance(expected_forward, torch.Tensor)
                    and expected_forward.dtype is not tensor.dtype
                ):
                    skip_inplace = True

                # TODO: backward consistency only supported for single tensor outputs
                # TODO: backward consistency only checked on sample.input, not all
                #   tensor inputs
                # TODO: update to handle checking grads of all tensor inputs as
                #   derived from each tensor output
                if isinstance(
                    expected_forward, torch.Tensor
                ) and dtype in op.supported_backward_dtypes(torch.device(device).type):
                    out = output_process_fn_grad(expected_forward).sum()
                    if out.dtype.is_complex:
                        out = out.abs()
                    out.backward()
                    expected_grad = tensor.grad

                # Test eager consistency
                for variant in variants:
                    # Skips inplace ops
                    if variant in inplace_ops and skip_inplace:
                        continue

                    # Compares variant's forward
                    # Note: copies the to-be-modified input when testing the inplace variant
                    tensor.grad = None
                    cloned = (
                        clone_input_helper(sample.input)
                        if variant in inplace_ops
                        else sample.input
                    )

                    if variant in inplace_ops and sample.broadcasts_input:
                        with self.assertRaises(
                            RuntimeError,
                            msg=(
                                "inplace variant either incorrectly allowed "
                                f"resizing or you have marked the sample {sample.summary()}"
                                " incorrectly with `broadcasts_self=True"
                            ),
                        ):
                            variant_forward = variant(
                                cloned, *sample.args, **sample.kwargs
                            )
                        continue

                    if variant in operators and sample.kwargs:
                        # skip samples with kwargs for operator variants
                        continue

                    variant_forward = variant(cloned, *sample.args, **sample.kwargs)
                    self.assertEqual(expected_forward, variant_forward)

                    # Compares variant's backward
                    if expected_grad is not None and (
                        variant not in inplace_ops or op.supports_inplace_autograd
                    ):
                        out = output_process_fn_grad(variant_forward).sum()
                        if out.dtype.is_complex:
                            out = out.abs()
                        out.backward()
                        self.assertEqual(expected_grad, tensor.grad)