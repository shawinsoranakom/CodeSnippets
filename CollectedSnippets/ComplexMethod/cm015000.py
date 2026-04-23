def test_linalg_lu_solve(self, device, dtype):
        make_arg = partial(make_tensor, dtype=dtype, device=device)

        backends = ["default"]

        if torch.device(device).type == 'cuda':
            backends.append("cusolver")

        def gen_matrices():
            rhs = 3
            ns = (5, 2, 0)
            batches = ((), (0,), (1,), (2,), (2, 1), (0, 2))
            for batch, n in product(batches, ns):
                yield make_arg(batch + (n, n)), make_arg(batch + (n, rhs))
            # Shapes to exercise all the paths
            shapes = ((1, 64), (2, 128), (1025, 2))
            for b, n in shapes:
                yield make_arg((b, n, n)), make_arg((b, n, rhs))

        for A, B in gen_matrices():
            LU, pivots = torch.linalg.lu_factor(A)
            for backend in backends:
                torch.backends.cuda.preferred_linalg_library(backend)

                for left, adjoint in product((True, False), repeat=2):
                    B_left = B if left else B.mT
                    X = torch.linalg.lu_solve(LU, pivots, B_left, left=left, adjoint=adjoint)
                    A_adj = A.mH if adjoint else A
                    if left:
                        self.assertEqual(B_left, A_adj @ X)
                    else:
                        self.assertEqual(B_left, X @ A_adj)