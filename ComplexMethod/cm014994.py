def test_svd_lowrank(self, device, dtype):
        from torch.testing._internal.common_utils import random_lowrank_matrix, random_sparse_matrix

        if torch.version.hip and isRocmArchAnyOf(MI200_ARCH) and dtype is torch.complex128:
            self.skipTest("Currently failing on rocm mi200")

        def run_subtest(actual_rank, matrix_size, batches, device, svd_lowrank, **options):
            density = options.pop('density', 1)
            if isinstance(matrix_size, int):
                rows = columns = matrix_size
            else:
                rows, columns = matrix_size
            if density == 1:
                a_input = random_lowrank_matrix(actual_rank, rows, columns, *batches, device=device, dtype=dtype)
                a = a_input
            else:
                if batches != ():
                    raise AssertionError(f"batches should be () for density != 1, got {batches}")
                a_input = random_sparse_matrix(rows, columns, density, device=device, dtype=dtype)
                a = a_input.to_dense()

            q = min(*size)
            u, s, v = svd_lowrank(a_input, q=q, niter=3, **options)

            # check if u, s, v is a SVD
            u, s, v = u[..., :q], s[..., :q], v[..., :q]
            A = (u * s.unsqueeze(-2)).matmul(v.mH)
            self.assertEqual(A, a, rtol=1e-7, atol=2e-7)

            # check if svd_lowrank produces same singular values as linalg.svdvals
            U, S, Vh = torch.linalg.svd(a, full_matrices=False)
            V = Vh.mH
            self.assertEqual(s, S, rtol=5e-7, atol=1e-7)

            if density == 1:
                # actual_rank is known only for dense inputs
                #
                # check if pairs (u, U) and (v, V) span the same
                # subspaces, respectively
                u, v = u[..., :actual_rank], v[..., :actual_rank]
                U, V = U[..., :actual_rank], V[..., :actual_rank]
                expected_ones = u.mH.matmul(U).det().abs()
                self.assertEqual(expected_ones, torch.ones_like(expected_ones))
                self.assertEqual(v.mH.matmul(V).det().abs(), torch.ones_like(expected_ones))

        all_batches = [(), (1,), (3,), (2, 3)]
        for actual_rank, size, all_batches in [  # noqa: B020
                (2, (17, 4), all_batches),
                (4, (17, 4), all_batches),
                (4, (17, 17), all_batches),
                (10, (100, 40), all_batches),
                (7, (1000, 1000), [()]),
        ]:
            # dense input
            for batches in all_batches:
                run_subtest(actual_rank, size, batches, device, torch.svd_lowrank)
                if size != size[::-1]:
                    run_subtest(actual_rank, size[::-1], batches, device, torch.svd_lowrank)

        # sparse input
        for size in [(17, 4), (4, 17), (17, 17), (100, 40), (40, 100), (1000, 1000)]:
            for density in [0.005, 0.1]:
                run_subtest(None, size, (), device, torch.svd_lowrank, density=density)

        # jitting support
        jitted = torch.jit.script(torch.svd_lowrank)
        actual_rank, size, batches = 2, (17, 4), ()
        run_subtest(actual_rank, size, batches, device, jitted)