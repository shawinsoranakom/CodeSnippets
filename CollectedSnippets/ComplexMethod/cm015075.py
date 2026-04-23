def test_binary_op_with_scalar_self_support(self, device, dtype, op, is_fastpath):
        def clone(arg):
            if isinstance(arg, (list, tuple)):
                return [clone(a) for a in arg]
            if torch.is_tensor(arg):
                return arg.detach().clone().requires_grad_()
            else:
                return arg

        scalar_self_arg_test_complete = False
        for sample in op.sample_inputs(
            device,
            dtype,
            noncontiguous=not is_fastpath,
            allow_higher_dtype_scalars=True,
        ):
            (rhs_arg,) = sample.args
            kwargs = {} or sample.kwargs
            alpha = kwargs.pop("alpha", None)
            wrapped_op, ref, inplace_op, inplace_ref = self._get_funcs(op)
            if isinstance(rhs_arg, Number) and not scalar_self_arg_test_complete:
                scalar_self_arg_test_complete = True
                self._binary_test(
                    dtype,
                    wrapped_op,
                    ref,
                    [rhs_arg, sample.input],
                    is_fastpath,
                    False,
                    alpha=alpha,
                    scalar_self_arg=True,
                )
                if op.supports_autograd and dtype == torch.float32:
                    transformed_sample = sample.transform(
                        get_transform_func(
                            len(sample.input), dtype, device, is_fastpath
                        )
                    )
                    tensors = transformed_sample.input
                    (rhs_arg,) = transformed_sample.args
                    ref_tensors, ref_rhs_arg = clone(tensors), clone(rhs_arg)
                    sum(
                        wrapped_op(
                            [rhs_arg, tensors], is_cuda=False, expect_fastpath=False
                        )
                    ).mean().backward()
                    sum(ref.func(ref_rhs_arg, t) for t in ref_tensors).mean().backward()
                    self.assertEqual(
                        [t.grad for t in tensors], [t.grad for t in ref_tensors]
                    )