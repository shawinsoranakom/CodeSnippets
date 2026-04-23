def test_autograd_dense_output(self, device, dtype, op):
        if op.name == "mv" and no_mkl_sparse and self.device_type == 'cpu':
            self.skipTest("MKL Sparse is not available")

        samples = list(op.sample_inputs(device, dtype, requires_grad=True))

        # Fail early to prevent silent success with this test
        ndims_equals_2d = (s.input.ndim == 2 for s in samples)
        if not any(ndims_equals_2d):
            raise ValueError("Expected at least one 2D tensor in samples.")

        # Here we assume that the signature is op(sparse_input, dense_input) -> dense_output
        for sample in samples:
            # TODO: Remove detach once we have autograd support for CSR input
            sparse_input = sample.input.to_sparse_csr().detach()

            def fn(*args):
                output = op.gradcheck_wrapper(op.get_op(), sparse_input, *args, **sample.kwargs)
                if sample.output_process_fn_grad is not None:
                    return sample.output_process_fn_grad(output)
                return output

            self.assertTrue(torch.autograd.gradcheck(fn, sample.args, fast_mode=True))

            # noncontiguous
            args = [make_tensor(a.shape, device=device, dtype=dtype, noncontiguous=True, requires_grad=True) for a in sample.args]
            self.assertTrue(torch.autograd.gradcheck(fn, args, fast_mode=True))