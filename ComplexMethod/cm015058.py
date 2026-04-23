def run_test(a, b, upper, transpose, unitriangular, op_out):
            if unitriangular and self.device_type == 'cpu':
                # TODO: When unitriangular=True results are not correct on CPU
                return

            if not upper and self.device_type == 'cpu':
                # TODO: When upper=False some generated inputs might crash on CPU
                return

            actual = torch.triangular_solve(b, a, upper=upper, unitriangular=unitriangular, transpose=transpose)
            actual_X = actual.solution
            actual_A_clone = actual.cloned_coefficient
            self.assertTrue(actual_A_clone.numel() == 0)
            if a._nnz() == 0:
                self.assertTrue(actual_X.isnan().all())
                return

            # TODO: replace with torch method when implemented to_dense() on block sparse tensor
            a_bsr = sp.bsr_matrix(
                (
                    a.values().cpu().numpy(),
                    a.col_indices().cpu().numpy(),
                    a.crow_indices().cpu().numpy(),
                ),
                shape=a.shape,
            )
            expected_X, _ = torch.triangular_solve(
                b,
                torch.tensor(a_bsr.todense(), device=device),
                transpose=transpose,
                upper=upper,
                unitriangular=unitriangular)

            if expected_X.isnan().any():
                # TODO: zeros on the diagonal are not handled for CPU path
                # there's no way to query this info from MKL
                if self.device_type == 'cuda' and not TEST_WITH_ROCM:
                    self.assertTrue(actual_X.isnan().any() or actual_X.isinf().any())
                return

            self.assertEqual(actual_X, expected_X)

            out = torch.empty_like(b.mH if op_out and a.shape == b.shape else b)
            torch.triangular_solve(
                b, a,
                upper=upper, unitriangular=unitriangular, transpose=transpose, out=(out, actual_A_clone)
            )
            self.assertEqual(out, actual_X)
            self.assertEqual(out, expected_X)