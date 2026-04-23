def test_init_gradient_and_hessians(loss, sample_weight, dtype, order):
    """Test that init_gradient_and_hessian works as expected.

    passing sample_weight to a loss correctly influences the constant_hessian
    attribute, and consequently the shape of the hessian array.
    """
    n_samples = 5
    if sample_weight == "range":
        sample_weight = np.ones(n_samples)
    loss = loss(sample_weight=sample_weight)
    gradient, hessian = loss.init_gradient_and_hessian(
        n_samples=n_samples,
        dtype=dtype,
        order=order,
    )
    if loss.constant_hessian:
        assert gradient.shape == (n_samples,)
        assert hessian.shape == (1,)
    elif loss.is_multiclass:
        assert gradient.shape == (n_samples, loss.n_classes)
        assert hessian.shape == (n_samples, loss.n_classes)
    else:
        assert hessian.shape == (n_samples,)
        assert hessian.shape == (n_samples,)

    assert gradient.dtype == dtype
    assert hessian.dtype == dtype

    if order == "C":
        assert gradient.flags.c_contiguous
        assert hessian.flags.c_contiguous
    else:
        assert gradient.flags.f_contiguous
        assert hessian.flags.f_contiguous