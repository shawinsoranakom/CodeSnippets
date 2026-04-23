def run_test(A, pivot, singular, fn):
            k = min(A.shape[-2:])
            batch = A.shape[:-2]
            check_errors = (fn == torch.linalg.lu_factor)
            if singular and check_errors:
                # It may or may not throw as the LU decomposition without pivoting
                # may still succeed for singular matrices
                try:
                    LU, pivots = fn(A, pivot=pivot)
                except RuntimeError:
                    return
            else:
                LU, pivots = fn(A, pivot=pivot)[:2]

            self.assertEqual(LU.size(), A.shape)
            self.assertEqual(pivots.size(), batch + (k,))

            if not pivot:
                self.assertEqual(pivots, torch.arange(1, 1 + k, device=device, dtype=torch.int32).expand(batch + (k, )))

            P, L, U = torch.lu_unpack(LU, pivots, unpack_pivots=pivot)

            self.assertEqual(P @ L @ U if pivot else L @ U, A)

            PLU = torch.linalg.lu(A, pivot=pivot)
            self.assertEqual(P, PLU.P)
            self.assertEqual(L, PLU.L)
            self.assertEqual(U, PLU.U)

            if not singular and A.size(-2) == A.size(-1):
                nrhs = ((), (1,), (3,))
                for left, rhs in product((True, False), nrhs):
                    # Vector case when left = False is not allowed
                    if not left and rhs == ():
                        continue
                    if left:
                        shape_B = A.shape[:-1] + rhs
                    else:
                        shape_B = A.shape[:-2] + rhs + A.shape[-1:]
                    B = make_arg(shape_B)

                    # Test linalg.lu_solve. It does not support vectors as rhs
                    # See https://github.com/pytorch/pytorch/pull/74045#issuecomment-1112304913
                    if rhs != ():
                        for adjoint in (True, False):
                            X = torch.linalg.lu_solve(LU, pivots, B, left=left, adjoint=adjoint)
                            A_adj = A.mH if adjoint else A
                            if left:
                                self.assertEqual(B, A_adj @ X)
                            else:
                                self.assertEqual(B, X @ A_adj)

                    # Test linalg.solve
                    X = torch.linalg.solve(A, B, left=left)
                    X_ = X.unsqueeze(-1) if rhs == () else X
                    B_ = B.unsqueeze(-1) if rhs == () else B
                    if left:
                        self.assertEqual(B_, A @ X_)
                    else:
                        self.assertEqual(B_, X_ @ A)