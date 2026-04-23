def test_noncontiguous_samples(self, device, dtype, op):
        test_grad = dtype in op.supported_backward_dtypes(torch.device(device).type)
        sample_inputs = op.sample_inputs(device, dtype, requires_grad=test_grad)
        for sample_input in sample_inputs:
            t_inp, t_args, t_kwargs = (
                sample_input.input,
                sample_input.args,
                sample_input.kwargs,
            )
            noncontig_sample = sample_input.noncontiguous()
            n_inp, n_args, n_kwargs = (
                noncontig_sample.input,
                noncontig_sample.args,
                noncontig_sample.kwargs,
            )

            # validates forward
            expected = op(t_inp, *t_args, **t_kwargs)
            actual = op(n_inp, *n_args, **n_kwargs)

            self.assertEqual(actual, expected)

            # Validate backward
            # Short-circuits if the op doesn't support grad in this device x dtype
            if not test_grad:
                continue

            expected = sample_input.output_process_fn_grad(expected)
            actual = sample_input.output_process_fn_grad(actual)

            if isinstance(expected, torch.Tensor):
                grad_for_expected = torch.randn_like(expected)
                grad_for_actual = noncontiguous_like(grad_for_expected)
            elif isinstance(expected, Sequence):
                # Filter output elements that do not require grad
                expected = [
                    t
                    for t in expected
                    if isinstance(t, torch.Tensor) and t.requires_grad
                ]
                actual = [
                    n for n in actual if isinstance(n, torch.Tensor) and n.requires_grad
                ]
                grad_for_expected = [torch.randn_like(t) for t in expected]
                grad_for_actual = [noncontiguous_like(n) for n in grad_for_expected]
            else:
                # Nothing to do if it returns a scalar or things like that
                continue

            # Concatenate inputs into a tuple
            t_inputs = (
                (t_inp,) + t_args
                if isinstance(t_inp, torch.Tensor)
                else tuple(t_inp) + t_args
            )
            n_inputs = (
                (n_inp,) + n_args
                if isinstance(n_inp, torch.Tensor)
                else tuple(n_inp) + n_args
            )

            # Filter the elements that are tensors that require grad
            t_input_tensors = [
                t for t in t_inputs if isinstance(t, torch.Tensor) and t.requires_grad
            ]
            n_input_tensors = [
                n for n in n_inputs if isinstance(n, torch.Tensor) and n.requires_grad
            ]

            self.assertEqual(len(t_input_tensors), len(n_input_tensors))

            # Some functions may not use all the inputs to generate gradients. One of the
            # few examples of this "odd" behaviour is F.hinge_embedding_loss
            t_grads = torch.autograd.grad(
                expected, t_input_tensors, grad_for_expected, allow_unused=True
            )
            n_grads = torch.autograd.grad(
                actual, n_input_tensors, grad_for_actual, allow_unused=True
            )

            msg = "Got different gradients for contiguous / non-contiguous inputs wrt input {}."
            for i, (t, n) in enumerate(zip(t_grads, n_grads)):
                self.assertEqual(t, n, msg=msg.format(i))