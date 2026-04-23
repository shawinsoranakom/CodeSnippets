def test_autograd_dense_output_addmm(self, device, dtype):
        from torch.testing._internal.common_methods_invocations import sample_inputs_addmm

        samples = list(sample_inputs_addmm(None, device, dtype, requires_grad=True))

        # Fail early to prevent silent success with this test
        ndims_equals_2d = (s.args[0].ndim == 2 for s in samples)
        if not any(ndims_equals_2d):
            raise ValueError("Expected at least one 2D tensor in samples to convert to sparse.")

        for sample in samples:
            a = sample.args[0].relu().to_sparse_csr()
            if sample.args[0].shape == sample.args[1].shape:
                import warnings
                warnings.warn("Broken for square matrices, see https://github.com/pytorch/pytorch/issues/116565")
                continue

            # This path tests the autograd path wrt dense inputs
            for addmm in [torch.addmm, torch.sparse.addmm]:

                def fn(c, b):
                    output = addmm(c, a, b, **sample.kwargs)
                    if sample.output_process_fn_grad is not None:
                        return sample.output_process_fn_grad(output)
                    return output

                self.assertTrue(torch.autograd.gradcheck(fn, [sample.input, sample.args[1]], fast_mode=True))

                # noncontiguous
                c = make_tensor(sample.input.shape, device=device, dtype=dtype, noncontiguous=True, requires_grad=True)
                b = make_tensor(sample.args[1].shape, device=device, dtype=dtype, noncontiguous=True, requires_grad=True)
                self.assertTrue(torch.autograd.gradcheck(fn, [c, b], fast_mode=True))

                # Now test the autograd path wrt sparse inputs
                for reverse in [True, False]:
                    c, b = sample.input, sample.args[1]
                    if reverse and a.shape != b.shape:
                        continue

                    def fn(a):
                        inputs = (c, b, a) if reverse else (c, a, b)
                        output = addmm(*inputs, **sample.kwargs)
                        if sample.output_process_fn_grad is not None:
                            return sample.output_process_fn_grad(output)
                        return output

                    # gradcheck doesn't work for sparse CSR yet, compare against dense path
                    # Compute sparse result
                    a = a.detach().requires_grad_(True)
                    output = fn(a)
                    covector = torch.randn_like(output)
                    output.backward(covector)
                    self.assertTrue(torch.is_tensor(a.grad))
                    if addmm == torch.sparse.addmm:
                        self.assertTrue(a.grad.is_sparse_csr)
                    else:
                        self.assertTrue(a.grad.layout == torch.strided)

                    # Compute dense result and compare with sparse result
                    dense_a = a.detach().to_dense().requires_grad_(True)
                    dense_output = fn(dense_a)
                    self.assertEqual(output, dense_output)
                    dense_covector = covector.to_dense()
                    dense_output.backward(dense_covector)

                    if addmm == torch.sparse.addmm:
                        self.assertEqual(a.grad, dense_a.grad.sparse_mask(a))
                    else:
                        self.assertEqual(a.grad, dense_a.grad)