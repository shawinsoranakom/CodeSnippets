def test_set_get_params(kernel):
    kernel = clone(kernel)  # make tests independent of one-another
    # Check that set_params()/get_params() is consistent with kernel.theta.

    # Test get_params()
    index = 0
    params = kernel.get_params()
    for hyperparameter in kernel.hyperparameters:
        if isinstance("string", type(hyperparameter.bounds)):
            if hyperparameter.bounds == "fixed":
                continue
        size = hyperparameter.n_elements
        if size > 1:  # anisotropic kernels
            assert_almost_equal(
                np.exp(kernel.theta[index : index + size]), params[hyperparameter.name]
            )
            index += size
        else:
            assert_almost_equal(
                np.exp(kernel.theta[index]), params[hyperparameter.name]
            )
            index += 1
    # Test set_params()
    index = 0
    value = 10  # arbitrary value
    for hyperparameter in kernel.hyperparameters:
        if isinstance("string", type(hyperparameter.bounds)):
            if hyperparameter.bounds == "fixed":
                continue
        size = hyperparameter.n_elements
        if size > 1:  # anisotropic kernels
            kernel.set_params(**{hyperparameter.name: [value] * size})
            assert_almost_equal(
                np.exp(kernel.theta[index : index + size]), [value] * size
            )
            index += size
        else:
            kernel.set_params(**{hyperparameter.name: value})
            assert_almost_equal(np.exp(kernel.theta[index]), value)
            index += 1