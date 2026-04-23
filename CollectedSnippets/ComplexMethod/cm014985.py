def test_linalg_lstsq(self, device, dtype):
        from torch.testing._internal.common_utils import random_well_conditioned_matrix
        if self.device_type == 'cpu':
            drivers = ('gels', 'gelsy', 'gelsd', 'gelss', None)
        else:
            drivers = ('gels', None)

        def check_solution_correctness(a, b, sol):
            sol2 = a.pinverse() @ b
            self.assertEqual(sol, sol2, atol=1e-5, rtol=1e-5)

        def check_correctness_ref(a, b, res, ref, driver="default"):
            def apply_if_not_empty(t, f):
                if t.numel():
                    return f(t)
                else:
                    return t

            def select_if_not_empty(t, i):
                selected = apply_if_not_empty(t, lambda x: x.select(0, i))
                return selected

            m = a.size(-2)
            n = a.size(-1)
            nrhs = b.size(-1)
            batch_size = int(np.prod(a.shape[:-2]))
            if batch_size == 0:
                batch_size = 1
            a_3d = a.view(batch_size, m, n)
            b_3d = b.view(batch_size, m, nrhs)

            solution_3d = res.solution.view(batch_size, n, nrhs)
            residuals_2d = apply_if_not_empty(res.residuals, lambda t: t.view(-1, nrhs))
            rank_1d = apply_if_not_empty(res.rank, lambda t: t.view(-1))
            singular_values_2d = res.singular_values.view(batch_size, res.singular_values.shape[-1])

            if a.numel() > 0:
                for i in range(batch_size):
                    sol, residuals, rank, singular_values = ref(
                        a_3d.select(0, i).numpy(),
                        b_3d.select(0, i).numpy()
                    )
                    # Singular values are None when lapack_driver='gelsy' in SciPy
                    if singular_values is None:
                        singular_values = []
                    self.assertEqual(sol, solution_3d.select(0, i), atol=1e-5, rtol=1e-5)
                    self.assertEqual(rank, select_if_not_empty(rank_1d, i), atol=1e-5, rtol=1e-5)
                    self.assertEqual(singular_values, singular_values_2d.select(0, i), atol=1e-5, rtol=1e-5)

                    # SciPy and NumPy operate only on non-batched input and
                    # return an empty array with shape (0,) if rank(a) != n
                    # in PyTorch the batched inputs are supported and
                    # matrices in the batched input can have different ranks
                    # we compute residuals only if all matrices have rank == n
                    # see https://github.com/pytorch/pytorch/issues/56483
                    if m > n:
                        if torch.all(rank_1d == n):
                            self.assertEqual(
                                residuals, select_if_not_empty(residuals_2d, i), atol=1e-5, rtol=1e-5, exact_dtype=False
                            )
                        else:
                            self.assertTrue(residuals_2d.numel() == 0)

            else:
                self.assertEqual(res.solution.shape, (*a.shape[:-2], n, nrhs))
                self.assertEqual(res.rank.shape, a.shape[:-2])

                # residuals are not always computed (and have non-zero shape)
                if m > n and driver != "gelsy":
                    self.assertEqual(res.residuals.shape, (*a.shape[:-2], 0))
                else:
                    self.assertEqual(res.residuals.shape, (0, ))

                # singular_values are not always computed (and have non-zero shape)
                if driver == "default" or driver == "gelsd" or driver == "gelss":
                    self.assertEqual(res.singular_values.shape, (*a.shape[:-2], min(m, n)))
                else:
                    self.assertEqual(res.singular_values.shape, (0, ))

        def check_correctness_scipy(a, b, res, driver, cond):
            # SciPy provides 3 driver options: gelsd, gelss, gelsy
            if TEST_SCIPY and driver in ('gelsd', 'gelss', 'gelsy'):
                import scipy.linalg

                def scipy_ref(a, b):
                    return scipy.linalg.lstsq(a, b, lapack_driver=driver, cond=cond)
                check_correctness_ref(a, b, res, scipy_ref, driver=driver)

        def check_correctness_numpy(a, b, res, driver, rcond):
            # NumPy uses only gelsd routine
            if driver == 'gelsd':

                def numpy_ref(a, b):
                    return np.linalg.lstsq(a, b, rcond=rcond)
                check_correctness_ref(a, b, res, numpy_ref)

        ms = [2 ** i for i in range(5)]
        m_ge_n_sizes = [(m, m // 2) for m in ms] + [(m, m) for m in ms]
        # cases m < n are only supported on CPU and for cuSOLVER path on CUDA
        m_l_n_sizes = [(m // 2, m) for m in ms]
        include_m_l_n_case = (has_cusolver() or device == 'cpu')
        matrix_sizes = m_ge_n_sizes + (m_l_n_sizes if include_m_l_n_case else [])
        batches = [(), (2,), (2, 2), (2, 2, 2)]
        # we generate matrices with singular values sampled from a normal distribution,
        # that is why we use `cond=1.0`, the mean to cut roughly half of all
        # the singular values and compare whether torch.linalg.lstsq agrees with
        # SciPy and NumPy.
        # if rcond is True then set value for it based on the used algorithm
        # rcond == -1 or any other negative value forces LAPACK to use machine precision tolerance
        rconds = (None, True, -1)

        for batch, matrix_size, driver, rcond in itertools.product(batches, matrix_sizes, drivers, rconds):
            # keep the rcond value if it is None or -1, set the driver specific value if it is True
            if rcond and rcond != -1:
                if driver in ('gelss', 'gelsd'):
                    # SVD based algorithm; set to zero roughly half of all the singular values
                    rcond = 1.0
                else:
                    # driver == 'gelsy'
                    # QR based algorithm; setting the value too high might lead to non-unique solutions and flaky tests
                    # so we skip this case
                    continue

            # specifying rcond value has no effect for gels driver so no need to run the tests again
            if driver == 'gels' and rcond is not None:
                continue

            shape = batch + matrix_size
            a = random_well_conditioned_matrix(*shape, dtype=dtype, device=device)
            b = torch.rand(*shape, dtype=dtype, device=device)

            m = a.size(-2)
            n = a.size(-1)
            res = torch.linalg.lstsq(a, b, rcond=rcond, driver=driver)
            sol = res.solution

            # Only checks gelsd, gelss, gelsy drivers
            check_correctness_scipy(a, b, res, driver, rcond)

            # Only checks gelsd driver
            check_correctness_numpy(a, b, res, driver, rcond)

            # gels driver is not checked by comparing to NumPy or SciPy implementation
            # because NumPy and SciPy do not implement this driver
            if driver == 'gels' and rcond is None:
                check_solution_correctness(a, b, sol)