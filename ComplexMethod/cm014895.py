def test_output_grad_match(self, device, dtype, op):
        self.assertEqual(device, "mps:0")

        for mps_sample in op.sample_inputs(
                device, dtype,
                requires_grad=(dtype.is_floating_point or dtype.is_complex),
                set_seed=True):
            #
            # Forward check
            #
            mps_out, cpu_out, cpu_sample = self._run_op(op, mps_sample)

            if op.name == "unique" and cpu_sample.kwargs["sorted"] is False:
                continue

            atol, rtol = self._compute_tolerances(op, dtype)
            if op.name in ["renorm", "norm", "linalg.norm"] and dtype == torch.float16:
                atol = 7e-4
                rtol = 1.5e-3

            self.assertEqual(cpu_out, mps_out, atol=atol, rtol=rtol)

            #
            # Backward check
            #
            cpu_args = [cpu_sample.input] + list(cpu_sample.args)
            mps_args = [mps_sample.input] + list(mps_sample.args)
            cpu_out = (cpu_out,) if isinstance(cpu_out, torch.Tensor) else tuple(cpu_out)
            mps_out = (mps_out,) if isinstance(mps_out, torch.Tensor) else tuple(mps_out)

            def req_grad(t):
                return isinstance(t, torch.Tensor) and t.requires_grad

            diff_cpu_out = tuple(t for t in cpu_out if req_grad(t))
            diff_mps_out = tuple(t for t in mps_out if req_grad(t))
            diff_cpu_arg = tuple(t for t in pytree.tree_leaves((cpu_args, cpu_sample.kwargs)) if req_grad(t))
            diff_mps_arg = tuple(t for t in pytree.tree_leaves((mps_args, mps_sample.kwargs)) if req_grad(t))
            self.assertEqual(len(diff_cpu_out), len(diff_mps_out))
            self.assertEqual(len(diff_cpu_arg), len(diff_mps_arg))

            if len(diff_cpu_out) == 0:
                continue
            # rand_like does not work with certain dtypes, so cast to double and cast back
            cpu_grad_outputs = tuple(torch.rand_like(t, dtype=torch.double).to(dtype=t.dtype) for t in diff_cpu_out)
            mps_grad_outputs = tuple(t.to("mps") for t in cpu_grad_outputs)

            # Compare computed gradients with cpu given random grad_output vector
            # Sometimes when the derivative is 0, we just don't bother creating the graph
            # allow_unused is needed in those cases.
            cpu_grad_inputs = torch.autograd.grad(diff_cpu_out, diff_cpu_arg, grad_outputs=cpu_grad_outputs, allow_unused=True)
            mps_grad_inputs = torch.autograd.grad(diff_mps_out, diff_mps_arg, grad_outputs=mps_grad_outputs, allow_unused=True)

            if (
                op.name == "nn.functional.pad"
                and op.variant_test_name in ["replicate", "reflect"]
                and dtype == torch.float16
            ):
                atol = 1e-5
                rtol = 1.5e-3
            if op.name == "nn.functional.unfold" and dtype == torch.float16:
                atol, rtol = 1e-3, 1e-3
            # Order of ops in unsafe_masked_index backward is not guaranteed
            # which leads to larger errors
            if op.name == "_unsafe_masked_index" and dtype == torch.float16:
                atol, rtol = 3e-3, 3e-3
            if op.name == "logcumsumexp":
                atol, rtol = 4e-3, 1e-3
            if op.name == "nn.functional.max_pool3d" and dtype == torch.float16:
                # In a few cases where stride is smaller than kernel size,
                # several output grad elements of similar magnitudes get summed
                # together, introducing significant error for float16.
                atol, rtol = 5e-3, 5e-3
            if op.name == "nn.functional.embedding_bag" and dtype == torch.float16:
                atol, rtol = 5e-3, 5e-3
            if op.name == "index_reduce" and op.variant_test_name in ['mean', 'prod'] and dtype in [torch.float16]:
                atol, rtol = 0.02, 0.02

            if isinstance(cpu_sample.input, torch.Tensor):
                equal_input_types = cpu_sample.input.dtype == mps_sample.input.dtype
            else:
                # TODO: Handle list inputs later
                equal_input_types = True
            self.assertEqual(cpu_grad_inputs, mps_grad_inputs, atol=atol, rtol=rtol, exact_dtype=equal_input_types)