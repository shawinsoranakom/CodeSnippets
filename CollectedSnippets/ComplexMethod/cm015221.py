def test_grad(self, device, dtype, op):
        if op.name in vjp_fail:
            self.skipTest("Skipped; Expected failures")
            return

        if not op.supports_autograd:
            self.skipTest("Skipped! Autograd not supported.")
            return

        samples = op.sample_inputs(device, dtype, requires_grad=True)

        if is_inplace(op, op.get_op()):
            self.skipTest("Skipped for redundancy. test_vjp handles in-place testing.")
            return

        for sample in samples:
            args = [sample.input] + list(sample.args)
            kwargs = sample.kwargs

            if op.name not in skip_noncontig:
                noncontig_sample = sample.noncontiguous()
                noncontig_args = [noncontig_sample.input] + list(noncontig_sample.args)
                noncontig_kwargs = noncontig_sample.kwargs

            diff_argnums = tuple(i for i, arg in enumerate(args) if diff_arg(arg))
            if len(diff_argnums) == 0:
                raise AssertionError("Expected at least one differentiable argument")
            diff_args = tuple(args[i] for i in diff_argnums)

            def wrapped_fn(*args, **kwargs):
                result = op(*args, **kwargs)
                if sample.output_process_fn_grad is not None:
                    result = sample.output_process_fn_grad(result)

                def abs_if_complex(t):
                    if t.dtype.is_complex:
                        return t.abs()
                    return t

                # Reduce into single value for grad
                if isinstance(result, torch.Tensor):
                    return abs_if_complex(result.sum())
                result = sum(abs_if_complex(res.sum()) for res in result)
                return result

            result = grad(wrapped_fn, diff_argnums)(*args, **kwargs)
            expected = _autograd_grad(_as_tuple(wrapped_fn(*args, **kwargs)), diff_args)
            self.assertEqual(result, expected)

            if op.name not in skip_noncontig:
                result_noncontig = grad(wrapped_fn, diff_argnums)(
                    *noncontig_args, **noncontig_kwargs
                )
                self.assertEqual(result_noncontig, expected)