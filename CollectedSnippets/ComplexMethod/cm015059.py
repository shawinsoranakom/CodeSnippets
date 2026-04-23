def run_test(n, k, upper, unitriangular, transpose, zero):
            if not unitriangular:
                triangle_function = torch.triu if upper else torch.tril
            else:
                # Make sure diagonal elements are not materialized.
                # This is to exercise `unitriangular=True` not relying on
                # explicit presence of these indices.
                if upper:
                    def remove_diagonal(t):
                        return t.triu(-1)

                else:
                    def remove_diagonal(t):
                        return t.tril(-1)

                triangle_function = remove_diagonal

            make_A = torch.zeros if zero else make_tensor
            A = make_A((n, n), dtype=dtype, device=device)
            A = triangle_function(A)
            A_sparse = A.to_sparse_csr()
            B = make_tensor((n, k), dtype=dtype, device=device)

            expected = torch.triangular_solve(B, A, upper=upper, unitriangular=unitriangular, transpose=transpose)
            expected_X = expected.solution

            actual = torch.triangular_solve(B, A_sparse, upper=upper, unitriangular=unitriangular, transpose=transpose)
            actual_X = actual.solution
            actual_A_clone = actual.cloned_coefficient
            self.assertTrue(actual_A_clone.numel() == 0)
            if A_sparse._nnz() == 0:
                self.assertTrue(actual_X.isnan().all())
                return
            self.assertEqual(actual_X, expected_X)

            # test out with C contiguous strides
            out = torch.empty_strided((n, k), (k, 1), dtype=dtype, device=device)
            torch.triangular_solve(
                B, A_sparse,
                upper=upper, unitriangular=unitriangular, transpose=transpose, out=(out, actual_A_clone)
            )
            self.assertEqual(out, expected_X)

            # test out with F contiguous strides
            out = torch.empty_strided((n, k), (1, n), dtype=dtype, device=device)
            torch.triangular_solve(
                B, A_sparse,
                upper=upper, unitriangular=unitriangular, transpose=transpose, out=(out, actual_A_clone)
            )
            self.assertEqual(out, expected_X)
            self.assertEqual(out.stride(), (1, n))

            # test out with discontiguous strides
            out = torch.empty_strided((2 * n, k), (1, 2 * n), dtype=dtype, device=device)[::2]
            if n > 0 and k > 0:
                self.assertFalse(out.is_contiguous())
                self.assertFalse(out.t().is_contiguous())
            before_stride = out.stride()
            torch.triangular_solve(
                B, A_sparse,
                upper=upper, unitriangular=unitriangular, transpose=transpose, out=(out, actual_A_clone)
            )
            self.assertEqual(out, expected_X)
            self.assertEqual(out.stride(), before_stride)