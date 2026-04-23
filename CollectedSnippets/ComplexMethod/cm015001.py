def _test_lobpcg_method(self, device, dtype, method):
        from torch.testing._internal.common_utils import random_symmetric_pd_matrix, random_sparse_pd_matrix
        from torch._linalg_utils import matmul, qform
        from torch._lobpcg import lobpcg

        def test_tracker(worker):
            k = worker.iparams['k']
            nc = worker.ivars['converged_count']

            # Regression test for PR #152789 (fixes issue #101075)
            # Ensure rerr is non-negative at each iteration
            rerr = worker.tvars['rerr']
            self.assertGreaterEqual(rerr.min(), 0.)

            if k <= nc:
                tol = worker.fparams['tol']
                rerr = worker.tvars['rerr']
                X = worker.X
                E = worker.E
                B = worker.B
                A = worker.A
                dtype = X.dtype
                device = X.device

                # Check convergence
                self.assertLessEqual(rerr[:k].max(), tol)

                # Check B-orthogonality
                I = torch.eye(k, k, dtype=dtype, device=device)
                self.assertEqual(qform(B, X[:, :k]), I)

                # Check block equation
                self.assertEqual(qform(A, X[:, :k]) / E[:k], I, atol=0.2, rtol=0)

        orig_lobpcg = lobpcg

        def lobpcg(*args, **kwargs):
            kwargs['tracker'] = test_tracker
            kwargs['niter'] = 1000
            kwargs['method'] = method
            kwargs['tol'] = 1e-8
            return orig_lobpcg(*args, **kwargs)
        prec = 5e-4
        mm = torch.matmul

        # Regression test for PR #152789 (fixes issue #101075)
        # https://github.com/pytorch/pytorch/issues/101075#issuecomment-1548483685
        # Demonstrates the original bug: negative residuals in the 2nd iteration
        A = torch.Tensor([
            [-0.56142016, 0.29639858, -0.16059532],
            [0.29639858, -0.69093563, 0.26248195],
            [-0.16059532, 0.26248195, -0.40236716]
        ])
        B = torch.Tensor([
            [1.89193057, -0.08174309, -0.3557846],
            [-0.08174309, 1.64589643, -0.46436347],
            [-0.3557846, -0.46436347, 1.67404367]
        ])
        X = torch.Tensor([[0.61591334, 0.63823109, 0.46185694]]).T
        E, V = lobpcg(A=A, B=B, X=X, k=1)
        self.assertEqual(matmul(A, V), mm(matmul(B, V), E.diag_embed()), atol=prec, rtol=0)

        # check dense input
        for batches in [(), (2,), (2, 3)]:
            for m, n, k in [
                    (9, 3, 1),
                    (9, 3, 2),
                    (9, 2, 2),
                    (100, 15, 5),
            ]:
                # skip tests that are known to fail with the basic
                # LOBPCG method due to calling cholesky on singular
                # input
                if method == 'basic' and (m, n, k) in [(9, 2, 2), (100, 15, 5)]:
                    continue
                A = random_symmetric_pd_matrix(m, *batches, device=device, dtype=dtype)
                B = random_symmetric_pd_matrix(m, *batches, device=device, dtype=dtype)

                # classical eigenvalue problem, smallest eigenvalues
                E, V = lobpcg(A, k=k, n=n, largest=False)
                self.assertEqual(E.shape, batches + (k,))
                self.assertEqual(V.shape, batches + (m, k))
                self.assertEqual(matmul(A, V), mm(V, E.diag_embed()), atol=prec, rtol=0)
                e = torch.linalg.eigvalsh(A)
                e_smallest = e[..., :k]
                self.assertEqual(E, e_smallest)

                # classical eigenvalue problem, largest eigenvalues
                E, V = lobpcg(A, k=k, n=n, largest=True)
                e_largest, _ = torch.sort(e[..., -k:], descending=True)
                self.assertEqual(E, e_largest, atol=prec, rtol=0)
                self.assertEqual(matmul(A, V), mm(V, E.diag_embed()), atol=prec, rtol=0)

                # generalized eigenvalue problem, smallest eigenvalues
                E, V = lobpcg(A, B=B, k=k, n=n, largest=False)
                self.assertEqual(matmul(A, V), mm(matmul(B, V), E.diag_embed()), atol=prec, rtol=0)

                # generalized eigenvalue problem, largest eigenvalues
                E, V = lobpcg(A, B=B, k=k, n=n, largest=True)
                self.assertEqual(matmul(A, V) / E.max(), mm(matmul(B, V), (E / E.max()).diag_embed()),
                                 atol=prec, rtol=0)

        # check sparse input
        for m, n, k, density in [
                (5, 1, 1, 0.8),
                (9, 3, 2, 0.5),
                (100, 1, 1, 0.1),
                (1000, 7, 3, 0.01),
        ]:
            # skip tests that are known to fail with the basic LOBCG
            # method due to insufficient accuracy
            if method == 'basic' and (m, n, k, density) == (1000, 7, 3, 0.01):
                continue
            A = random_sparse_pd_matrix(m, density=density, device=device, dtype=dtype)
            B = random_sparse_pd_matrix(m, density=density, device=device, dtype=dtype)
            A_eigenvalues = torch.arange(1, m + 1, dtype=dtype) / m
            e_smallest = A_eigenvalues[..., :k]
            e_largest, _ = torch.sort(A_eigenvalues[..., -k:], descending=True)

            # classical eigenvalue problem, smallest eigenvalues
            E, V = lobpcg(A, k=k, n=n, largest=False)
            self.assertEqual(E, e_smallest)
            self.assertEqual(matmul(A, V), mm(V, E.diag_embed()), atol=prec, rtol=0)

            # classical eigenvalue problem, largest eigenvalues
            E, V = lobpcg(A, k=k, n=n, largest=True)
            self.assertEqual(matmul(A, V), mm(V, E.diag_embed()), atol=prec, rtol=0)
            self.assertEqual(E, e_largest)

            # generalized eigenvalue problem, smallest eigenvalues
            E, V = lobpcg(A, B=B, k=k, n=n, largest=False)
            self.assertEqual(matmul(A, V), matmul(B, mm(V, E.diag_embed())), atol=prec, rtol=0)

            # generalized eigenvalue problem, largest eigenvalues
            E, V = lobpcg(A, B=B, k=k, n=n, largest=True)
            self.assertEqual(matmul(A, V) / E.max(), mm(matmul(B, V), (E / E.max()).diag_embed()),
                             atol=prec, rtol=0)