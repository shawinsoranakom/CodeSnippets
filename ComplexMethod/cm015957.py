def test_orthogonal_parametrization(self):
        # Orthogonal implements 6 algorithms (3x parametrizations times 2 options of use_trivialization)

        def assert_is_orthogonal(X):
            n, k = X.size(-2), X.size(-1)
            if n < k:
                X = X.mT
                n, k = k, n
            Id = torch.eye(k, dtype=X.dtype, device=X.device).expand(
                *(X.size()[:-2]), k, k
            )
            eps = 10 * n * torch.finfo(X.dtype).eps
            torch.testing.assert_close(X.mH @ X, Id, atol=eps, rtol=0.0)

        def assert_weight_allclose_Q(weight, W):
            # Test that weight is equal to the Q part of the QR decomposition of W
            # (or of its transpose if the matrix is wide)
            wide_matrix = W.size(-2) < W.size(-1)
            if wide_matrix:
                W = W.mT
            Q, R = torch.linalg.qr(W)
            Q *= R.diagonal(dim1=-2, dim2=-1).sgn().unsqueeze(-2)
            if wide_matrix:
                Q = Q.mT
            torch.testing.assert_close(Q, weight, atol=1e-5, rtol=0.0)

        for shape, dtype, use_linear in product(
            ((4, 4), (5, 3), (3, 5)),  # square/ tall / wide
            (torch.float32, torch.complex64),
            (True, False),
        ):
            # Conv2d does not support complex yet
            if not use_linear:
                continue

            if use_linear:
                input = torch.randn(3, shape[0], dtype=dtype)
            else:
                input = torch.randn(2, 2, shape[0] + 2, shape[1] + 1, dtype=dtype)

            for parametrization, use_trivialization in product(
                ("matrix_exp", "cayley", "householder"), (False, True)
            ):
                # right_inverse for Cayley and matrix_exp not implemented for use_trivialization=False
                # See Note [right_inverse expm cayley]
                can_initialize = use_trivialization or parametrization == "householder"

                # We generate them every time to always start with fresh weights
                if use_linear:
                    m = nn.Linear(*shape, dtype=dtype)
                else:
                    m = nn.Conv2d(2, 3, shape, dtype=dtype)

                # We do not support householder for complex inputs
                # See Note [Householder complex]

                # When using the swap_tensors path, this is needed so that the autograd
                # graph is not alive anymore.
                if get_swap_module_params_on_conversion():
                    w_init = m.weight.detach().clone()
                else:
                    w_init = m.weight.clone()
                if parametrization == "householder" and m.weight.is_complex():
                    msg = "householder parametrization does not support complex tensors"
                    with self.assertRaisesRegex(ValueError, msg):
                        torch.nn.utils.parametrizations.orthogonal(
                            m,
                            "weight",
                            parametrization,
                            use_trivialization=use_trivialization,
                        )
                    continue

                wide_matrix = w_init.size(-2) < w_init.size(-1)
                torch.nn.utils.parametrizations.orthogonal(
                    m, "weight", parametrization, use_trivialization=use_trivialization
                )
                # Forwards works as expected
                self.assertEqual(w_init.shape, m.weight.shape)
                assert_is_orthogonal(m.weight)
                if can_initialize:
                    assert_weight_allclose_Q(m.weight, w_init)

                # Initializing with a given orthogonal matrix works
                X = torch.randn_like(m.weight)
                if wide_matrix:
                    X = X.mT
                w_new = torch.linalg.qr(X).Q
                if wide_matrix:
                    w_new = w_new.mT
                if can_initialize:
                    m.weight = w_new
                    torch.testing.assert_close(w_new, m.weight, atol=1e-5, rtol=0.0)
                else:
                    msg = (
                        "assign to the matrix exponential or the Cayley parametrization"
                    )
                    with self.assertRaisesRegex(NotImplementedError, msg):
                        m.weight = w_new

                # Initializing with a non-orthogonal matrix makes m.weight be the Q part of the given matrix
                w_new = torch.randn_like(m.weight)
                if can_initialize:
                    m.weight = w_new
                    assert_weight_allclose_Q(m.weight, w_new)
                else:
                    msg = (
                        "assign to the matrix exponential or the Cayley parametrization"
                    )
                    with self.assertRaisesRegex(NotImplementedError, msg):
                        m.weight = w_new

                opt = torch.optim.SGD(m.parameters(), lr=0.1)
                for _ in range(2):
                    opt.zero_grad()
                    m(input).norm().backward()
                    grad = m.parametrizations.weight.original.grad
                    self.assertIsNotNone(grad)
                    # We do not update the upper triangular part of the matrix if tall tril if wide
                    if grad.size(-2) >= grad.size(-1):
                        zeros_grad = grad.triu(1)
                    else:
                        zeros_grad = grad.tril(-1)
                    self.assertEqual(zeros_grad, torch.zeros_like(zeros_grad))
                    # The gradient in the diagonal can only be imaginary because a skew-Hermitian
                    # matrix has imaginary diagonal
                    diag_grad = grad.diagonal(dim1=-2, dim2=-1)
                    if grad.is_complex():
                        diag_grad = diag_grad.real
                    self.assertEqual(diag_grad, torch.zeros_like(diag_grad))
                    opt.step()
                    assert_is_orthogonal(m.weight)