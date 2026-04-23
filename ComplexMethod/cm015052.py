def test_linalg_solve_sparse_csr_cusolver(self, device, dtype):
        # https://github.com/krshrimali/pytorch/blob/f5ee21dd87a7c5e67ba03bfd77ea22246cabdf0b/test/test_sparse_csr.py

        try:
            spd = torch.rand(4, 3)
            A = spd.T @ spd
            b = torch.rand(3).cuda()
            A = A.to_sparse_csr().cuda()
            x = torch.sparse.spsolve(A, b)
        except RuntimeError as e:
            if "Calling linear solver with sparse tensors requires compiling " in str(e):
                self.skipTest("PyTorch was not built with cuDSS support")

        samples = sample_inputs_linalg_solve(None, device, dtype)

        for sample in samples:
            if sample.input.ndim != 2:
                continue

            out = torch.zeros(sample.args[0].size(), dtype=dtype, device=device)
            if sample.args[0].ndim != 1 and sample.args[0].size(-1) != 1:
                with self.assertRaisesRegex(RuntimeError, "b must be a 1D tensor"):
                    out = torch.linalg.solve(sample.input.to_sparse_csr(), *sample.args, **sample.kwargs)
                break
            if not sample.args[0].numel():
                with self.assertRaisesRegex(RuntimeError,
                                            "Expected non-empty other tensor, but found empty tensor"):
                    torch.linalg.solve(sample.input.to_sparse_csr(), *sample.args, **sample.kwargs, out=out)
                break

            expect = torch.linalg.solve(sample.input, *sample.args, **sample.kwargs)
            sample.input = sample.input.to_sparse_csr()
            if sample.args[0].ndim != 1 and sample.args[0].size(-1) == 1:
                expect = expect.squeeze(-1)
                sample.args = (sample.args[0].squeeze(-1), )
            out = torch.linalg.solve(sample.input, *sample.args, **sample.kwargs)
            self.assertEqual(expect, out)