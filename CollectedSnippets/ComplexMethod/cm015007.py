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