def test_kernel_theta(kernel):
    # Check that parameter vector theta of kernel is set correctly.
    kernel = clone(kernel)  # make tests independent of one-another
    theta = kernel.theta
    _, K_gradient = kernel(X, eval_gradient=True)

    # Determine kernel parameters that contribute to theta
    init_sign = signature(kernel.__class__.__init__).parameters.values()
    args = [p.name for p in init_sign if p.name != "self"]
    theta_vars = map(
        lambda s: s[0 : -len("_bounds")], filter(lambda s: s.endswith("_bounds"), args)
    )
    assert set(hyperparameter.name for hyperparameter in kernel.hyperparameters) == set(
        theta_vars
    )

    # Check that values returned in theta are consistent with
    # hyperparameter values (being their logarithms)
    for i, hyperparameter in enumerate(kernel.hyperparameters):
        assert theta[i] == np.log(getattr(kernel, hyperparameter.name))

    # Fixed kernel parameters must be excluded from theta and gradient.
    for i, hyperparameter in enumerate(kernel.hyperparameters):
        # create copy with certain hyperparameter fixed
        params = kernel.get_params()
        params[hyperparameter.name + "_bounds"] = "fixed"
        kernel_class = kernel.__class__
        new_kernel = kernel_class(**params)
        # Check that theta and K_gradient are identical with the fixed
        # dimension left out
        _, K_gradient_new = new_kernel(X, eval_gradient=True)
        assert theta.shape[0] == new_kernel.theta.shape[0] + 1
        assert K_gradient.shape[2] == K_gradient_new.shape[2] + 1
        if i > 0:
            assert theta[:i] == new_kernel.theta[:i]
            assert_array_equal(K_gradient[..., :i], K_gradient_new[..., :i])
        if i + 1 < len(kernel.hyperparameters):
            assert theta[i + 1 :] == new_kernel.theta[i:]
            assert_array_equal(K_gradient[..., i + 1 :], K_gradient_new[..., i:])

    # Check that values of theta are modified correctly
    for i, hyperparameter in enumerate(kernel.hyperparameters):
        theta[i] = np.log(42)
        kernel.theta = theta
        assert_almost_equal(getattr(kernel, hyperparameter.name), 42)

        setattr(kernel, hyperparameter.name, 43)
        assert_almost_equal(kernel.theta[i], np.log(43))