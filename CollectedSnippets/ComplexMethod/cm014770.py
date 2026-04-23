def test_compile_backward(self, device, dtype, op):
        for sample, subtest_ctx, skip_xfail_ctx in op.sample_inputs(
            device=device, dtype=dtype, requires_grad=True, use_subtests=True
        ):
            with subtest_ctx(self), skip_xfail_ctx(self):
                torch.compiler.reset()

                op_fn = op.op

                def f(*args, **kwargs):
                    return op_fn(*args, **kwargs)

                compiled_f = torch.compile(
                    f, fullgraph=True, backend="aot_eager_decomp_partition"
                )

                out_ref = f(sample.input, *sample.args, **sample.kwargs)
                out_compile = compiled_f(sample.input, *sample.args, **sample.kwargs)
                if op._extra_op_data.is_view:
                    tree_map_only(
                        NestedTensor, lambda x: self.assertTrue(x._is_view()), out_ref
                    )

                if op.full_name in COMPARE_TENSOR_COMPONENT_EQUALITY:
                    self.assertEqualIgnoringNestedInts(out_compile, out_ref)
                else:
                    self.assertEqual(out_compile, out_ref)

                inps, _ = tree_flatten((sample.input, sample.args, sample.kwargs))
                g_inps = [
                    inp
                    for inp in inps
                    if isinstance(inp, torch.Tensor) and inp.requires_grad
                ]
                if len(g_inps) > 0:
                    need_grad_outs, grad_outputs = self._gen_grad_outputs(out_compile)
                    grads_compile = torch.autograd.grad(
                        need_grad_outs,
                        inputs=g_inps,
                        grad_outputs=grad_outputs,
                    )

                    need_grad_outs, grad_outputs = self._gen_grad_outputs(out_ref)
                    grads_ref = torch.autograd.grad(
                        need_grad_outs,
                        inputs=g_inps,
                        grad_outputs=grad_outputs,
                    )

                    self.assertEqualNoncontigAware(grads_compile, grads_ref)