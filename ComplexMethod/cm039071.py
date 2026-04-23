def test_gradients_hessians_numerically(loss, sample_weight, global_random_seed):
    """Test gradients and hessians with numerical derivatives.

    Gradient should equal the numerical derivatives of the loss function.
    Hessians should equal the numerical derivatives of gradients.
    """
    n_samples = 20
    y_true, raw_prediction = random_y_true_raw_prediction(
        loss=loss,
        n_samples=n_samples,
        y_bound=(-100, 100),
        raw_bound=(-5, 5),
        seed=global_random_seed,
    )

    if sample_weight == "range":
        sample_weight = np.linspace(1, y_true.shape[0], num=y_true.shape[0])

    g, h = loss.gradient_hessian(
        y_true=y_true,
        raw_prediction=raw_prediction,
        sample_weight=sample_weight,
    )

    assert g.shape == raw_prediction.shape
    assert h.shape == raw_prediction.shape

    if not loss.is_multiclass:

        def loss_func(x):
            return loss.loss(
                y_true=y_true,
                raw_prediction=x,
                sample_weight=sample_weight,
            )

        g_numeric = numerical_derivative(loss_func, raw_prediction, eps=1e-6)
        assert_allclose(g, g_numeric, rtol=5e-6, atol=1e-10)

        def grad_func(x):
            return loss.gradient(
                y_true=y_true,
                raw_prediction=x,
                sample_weight=sample_weight,
            )

        h_numeric = numerical_derivative(grad_func, raw_prediction, eps=1e-6)
        if loss.approx_hessian:
            # TODO: What could we test if loss.approx_hessian?
            pass
        else:
            assert_allclose(h, h_numeric, rtol=5e-6, atol=1e-10)
    else:
        # For multiclass loss, we should only change the predictions of the
        # class for which the derivative is taken for, e.g. offset[:, k] = eps
        # for class k.
        # As a softmax is computed, offsetting the whole array by a constant
        # would have no effect on the probabilities, and thus on the loss.
        for k in range(loss.n_classes):

            def loss_func(x):
                raw = raw_prediction.copy()
                raw[:, k] = x
                return loss.loss(
                    y_true=y_true,
                    raw_prediction=raw,
                    sample_weight=sample_weight,
                )

            g_numeric = numerical_derivative(loss_func, raw_prediction[:, k], eps=1e-5)
            assert_allclose(g[:, k], g_numeric, rtol=5e-6, atol=1e-10)

            def grad_func(x):
                raw = raw_prediction.copy()
                raw[:, k] = x
                return loss.gradient(
                    y_true=y_true,
                    raw_prediction=raw,
                    sample_weight=sample_weight,
                )[:, k]

            h_numeric = numerical_derivative(grad_func, raw_prediction[:, k], eps=1e-6)
            if loss.approx_hessian:
                # TODO: What could we test if loss.approx_hessian?
                pass
            else:
                assert_allclose(h[:, k], h_numeric, rtol=5e-6, atol=1e-10)