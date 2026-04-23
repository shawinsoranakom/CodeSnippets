def test_autodiff(self, device, dtype, op, inplace):
        if (not inplace) and not op.supports_out:
            self.skipTest("out-of-place not implemented")
        if inplace and op.has_no_in_place:
            self.skipTest("in-place not implemented")
        if not (
            op.supports_autograd
            or op.supports_inplace_autograd
            or op.supports_forward_ad
        ):
            self.skipTest("neither reverse mode nor forward mode supported")

        # note(crcrpar): without this, some unary functions fail, unlike inplace and/or complex.
        if (
            (not inplace)
            and dtype == torch.float64
            and op.name
            in (
                "_foreach_acos",
                "_foreach_asin",
                "_foreach_log10",
                "_foreach_log1p",
                "_foreach_log2",
                "_foreach_log",
                "_foreach_pow",
                "_foreach_sqrt",
                "_foreach_rsqrt",
            )
        ):
            value_range = {"low": 0.5, "high": 1.0}
        else:
            value_range = {}
        for sample in op.sample_inputs(
            device,
            dtype,
            requires_grad=True,
            num_input_tensors=[5],
            allow_higher_dtype_scalars=True,
            **value_range,
        ):
            # Skip `_foreach_pow.ScalarAndTensor(Scalar, Tensor[])`
            if op.name == "_foreach_pow" and isinstance(sample.input, Number):
                continue

            func = None
            if inplace:
                # Call `clone` to avoid inplace modifications likewise
                # `torch.testing._internal.common_utils.TestGradients._get_safe_inplace`
                def inplace_func(*tensorlist):
                    kwargs = (
                        {"alpha": sample.kwargs["alpha"]}
                        if "alpha" in sample.kwargs
                        else {}
                    )
                    op.inplace_variant(
                        tuple(t.clone() for t in tensorlist), *sample.args, **kwargs
                    )
                    return tensorlist

                func = inplace_func
            else:

                def outplace_func(*tensorlist):
                    kwargs = (
                        {"alpha": sample.kwargs["alpha"]}
                        if "alpha" in sample.kwargs
                        else {}
                    )
                    return op.method_variant(tensorlist, *sample.args, **kwargs)

                func = outplace_func

            working_sample, err_msg_pattern = check_autodiff_sample(
                op, sample, dtype, inplace
            )

            def call_gradcheck():
                gradcheck(
                    func,
                    sample.input,
                    raise_exception=True,
                    check_forward_ad=op.supports_forward_ad,
                    check_batched_forward_grad=False,
                    check_backward_ad=op.supports_autograd,
                    check_batched_grad=False,
                )

            if not working_sample:
                if not err_msg_pattern:
                    # lhs of float64 and rhs of complex.
                    continue
                with self.assertRaisesRegex(RuntimeError, re.escape(err_msg_pattern)):
                    call_gradcheck()
                continue
            call_gradcheck()

            # Test per-tensor `grad_fn` behavior.
            if inplace and op.supports_inplace_autograd:
                # per-tensor `grad_fn` check.
                hook_buffer = []

                def get_grad_fn_hook(i):
                    def hook(grad_inputs, grad_outputs) -> None:
                        hook_buffer.append(i)

                    return hook

                _inputs = [t.detach().clone().requires_grad_() for t in sample.input]
                inputs = [t.clone() for t in _inputs]
                kwargs = (
                    {"alpha": sample.kwargs["alpha"]}
                    if "alpha" in sample.kwargs
                    else {}
                )
                op.inplace_variant(inputs, *sample.args, **kwargs)

                self.assertEqual(len({t.grad_fn for t in inputs}), len(inputs))

                for i, t in enumerate(inputs):
                    t.grad_fn.register_hook(get_grad_fn_hook(i))

                torch.autograd.grad(
                    inputs[0],
                    inputs=(_inputs[0],),
                    grad_outputs=(torch.rand_like(inputs[0]),),
                    retain_graph=True,
                )
                self.assertEqual(hook_buffer, [0])
                hook_buffer.clear()

                # tensors have different shapes.
                sum_of_cloned_tensors = torch.cat([t.view(-1) for t in inputs]).sum()
                grad_output = torch.rand_like(sum_of_cloned_tensors)
                torch.autograd.grad(
                    sum_of_cloned_tensors,
                    inputs=tuple(_inputs),
                    grad_outputs=(grad_output,),
                    retain_graph=False,
                )
                self.assertEqual(hook_buffer, list(reversed(range(len(inputs)))))