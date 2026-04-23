def test_init_zero_coef(
    base_loss, fit_intercept, n_features, dtype, global_random_seed
):
    """Test that init_zero_coef initializes coef correctly."""
    loss = LinearModelLoss(base_loss=base_loss(), fit_intercept=fit_intercept)
    rng = np.random.RandomState(global_random_seed)
    X = rng.normal(size=(5, n_features))
    coef = loss.init_zero_coef(X, dtype=dtype)
    if loss.base_loss.is_multiclass:
        n_classes = loss.base_loss.n_classes
        assert coef.shape == (n_classes, n_features + fit_intercept)
        assert coef.flags["F_CONTIGUOUS"]
    else:
        assert coef.shape == (n_features + fit_intercept,)

    if dtype is None:
        assert coef.dtype == X.dtype
    else:
        assert coef.dtype == dtype

    assert np.count_nonzero(coef) == 0