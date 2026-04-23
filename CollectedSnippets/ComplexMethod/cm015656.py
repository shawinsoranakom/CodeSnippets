def _validate_compile(self, fn, arg_fn):
        def _gen_grad_outputs(out_val):
            if isinstance(out_val, (list, tuple)):
                return tuple(torch.ones_like(c) for c in out_val)
            else:
                return (torch.ones_like(out_val),)

        with self.branch_nested_state():
            from torch.nested._internal.nested_tensor import _tensor_symint_registry

            # Validate that compilation does not modify eager state
            registry_before = list(_tensor_symint_registry.items())
            count_before = torch.nested._internal.nested_tensor._tensor_id_counter

            guards_exported = []
            guards_failed = []

            def append_guard_export(guards):
                for g in guards:
                    if g.code_list is not None:
                        guards_exported.append(g.code_list[0])

            def append_guard_fail(guards):
                guards_failed.extend(guards)

            compiled = torch._dynamo.optimize(
                nopython=True,
                backend="aot_eager",
                guard_export_fn=append_guard_export,
                guard_fail_fn=append_guard_fail,
            )(fn)
            registry_after = list(_tensor_symint_registry.items())
            count_after = torch.nested._internal.nested_tensor._tensor_id_counter
            self.assertEqual(registry_before, registry_after)
            self.assertEqual(count_before, count_after)

            args = arg_fn()
            compile_out = compiled(*args)
            compile_grads = []
            g_args = [arg for arg in args if arg.requires_grad]
            if len(g_args) > 0:
                compile_grad_outputs = _gen_grad_outputs(compile_out)
                compile_grads = torch.autograd.grad(
                    compile_out, inputs=g_args, grad_outputs=compile_grad_outputs
                )

        with self.branch_nested_state():
            args = arg_fn()
            ref_out = fn(*args)
            ref_grads = []
            g_args = [arg for arg in args if arg.requires_grad]
            if len(g_args) > 0:
                ref_grad_outputs = _gen_grad_outputs(ref_out)
                ref_grads = torch.autograd.grad(
                    ref_out, inputs=g_args, grad_outputs=ref_grad_outputs
                )

        # Validate correctness forward
        if isinstance(compile_out, (list, tuple)):
            # TODO: Fix assertEqual() to support NJTs so this isn't necessary
            self.assertEqual(len(compile_out), len(ref_out))
            for c, r in zip(compile_out, ref_out):
                self.assertEqualIgnoringNestedInts(c, r)
        else:
            self.assertEqualIgnoringNestedInts(compile_out, ref_out)

        # Validate correctness backward
        for compile_grad, ref_grad in zip(compile_grads, ref_grads):
            self.assertEqualIgnoringNestedInts(compile_grad, ref_grad)

        return guards_exported, guards_failed