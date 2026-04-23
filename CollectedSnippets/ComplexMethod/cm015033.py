def _test_math_view(
        self,
        device,
        dtype,
        op,
        samples,
        math_op_physical,
        math_op_view,
        is_bit_set,
        out_type,
    ):
        inplace_variant = op.inplace_variant

        # helper function to clone and conjugate/negate the input if its a tensor
        # else clone the sequence and conjugate/negate the first element in the sequence
        # If a requires_grad argument is provided the tensor being conjugated/negated will
        # have its requires_grad set to that value.
        def clone_and_perform_view(input, **kwargs):
            if isinstance(input, torch.Tensor):
                requires_grad = kwargs.get("requires_grad", input.requires_grad)
                with torch.no_grad():
                    # Ensure view represents the original sample input
                    input = math_op_physical(input)
                # Note: .conj() is not called under no_grad mode since it's not allowed to modify a
                # view created in no_grad mode. Here it's ok to do so, so as a workaround we call conj
                # before resetting the requires_grad field for input
                input = math_op_view(input)
                if not input.is_leaf:
                    raise AssertionError("expected input to be a leaf tensor")
                return input.requires_grad_(requires_grad)

            if isinstance(input, Sequence):
                out = list(map(clone_input_helper, input))
                out[0] = clone_and_perform_view(out[0])
                return tuple(out)

        for sample in samples:
            tensor = (
                sample.input
                if isinstance(sample.input, torch.Tensor)
                else sample.input[0]
            )
            cloned1 = clone_and_perform_view(sample.input)

            # Computes function forward value with a physically conjugated/negated tensor and
            # a conj/neg view tensor and verifies that the output in both case are equal.
            expected_forward = op(sample.input, *sample.args, **sample.kwargs)
            forward_with_mathview = op(cloned1, *sample.args, **sample.kwargs)
            self.assertEqual(expected_forward, forward_with_mathview)

            # If the op has an inplace variant, and the input doesn't require broadcasting
            # and has the same dtype as output, verify that the inplace operation on a conjugated/negated
            # input produces correct output, and the output tensor has the conj/neg bit set to True
            if inplace_variant is not None and not sample.broadcasts_input:
                cloned2 = clone_and_perform_view(tensor, requires_grad=False)
                if (
                    isinstance(expected_forward, torch.Tensor)
                    and expected_forward.dtype is tensor.dtype
                ):
                    inplace_forward = inplace_variant(
                        cloned2, *sample.args, **sample.kwargs
                    )
                    self.assertTrue(is_bit_set(inplace_forward))
                    self.assertEqual(inplace_forward, expected_forward)

            # TODO: backward consistency only supported for single tensor outputs
            # TODO: backward consistency only checked on sample.input, not all
            #   tensor inputs
            # TODO: update to handle checking grads of all tensor inputs as
            #   derived from each tensor output
            if (
                isinstance(expected_forward, torch.Tensor)
                and expected_forward.requires_grad
            ):
                output_process_fn_grad = sample.output_process_fn_grad or (lambda x: x)
                expected_forward = output_process_fn_grad(expected_forward)
                forward_with_mathview = output_process_fn_grad(forward_with_mathview)

                tensor = (
                    sample.input
                    if isinstance(sample.input, torch.Tensor)
                    else sample.input[0]
                )
                expected_forward.sum().abs().backward(retain_graph=True)
                forward_with_mathview.sum().abs().backward(retain_graph=True)
                if tensor.grad is not None:
                    cloned1_tensor = (
                        cloned1 if isinstance(cloned1, torch.Tensor) else cloned1[0]
                    )
                    self.assertEqual(tensor.grad, cloned1_tensor.grad)

                    tensor.grad, cloned1_tensor.grad = None, None

                    # a repeat of the above test if output is not complex valued
                    if out_type(expected_forward):
                        grad = torch.randn_like(expected_forward)
                        expected_forward.backward(grad)
                        forward_with_mathview.backward(
                            math_op_view(math_op_physical(grad))
                        )

                        self.assertEqual(tensor.grad, cloned1_tensor.grad)