def test_loss_gradients_are_the_same(loss, sample_weight, global_random_seed):
    """Test that loss and gradient are the same across different functions.

    Also test that output arguments contain correct results.
    """
    y_true, raw_prediction = random_y_true_raw_prediction(
        loss=loss,
        n_samples=20,
        y_bound=(-100, 100),
        raw_bound=(-10, 10),
        seed=global_random_seed,
    )
    if sample_weight == "range":
        sample_weight = np.linspace(1, y_true.shape[0], num=y_true.shape[0])

    out_l1 = np.empty_like(y_true)
    out_l2 = np.empty_like(y_true)
    out_g1 = np.empty_like(raw_prediction)
    out_g2 = np.empty_like(raw_prediction)
    out_g3 = np.empty_like(raw_prediction)
    out_h3 = np.empty_like(raw_prediction)

    l1 = loss.loss(
        y_true=y_true,
        raw_prediction=raw_prediction,
        sample_weight=sample_weight,
        loss_out=out_l1,
    )
    g1 = loss.gradient(
        y_true=y_true,
        raw_prediction=raw_prediction,
        sample_weight=sample_weight,
        gradient_out=out_g1,
    )
    l2, g2 = loss.loss_gradient(
        y_true=y_true,
        raw_prediction=raw_prediction,
        sample_weight=sample_weight,
        loss_out=out_l2,
        gradient_out=out_g2,
    )
    g3, h3 = loss.gradient_hessian(
        y_true=y_true,
        raw_prediction=raw_prediction,
        sample_weight=sample_weight,
        gradient_out=out_g3,
        hessian_out=out_h3,
    )
    assert_allclose(l1, l2)
    assert_array_equal(l1, out_l1)
    assert np.shares_memory(l1, out_l1)
    assert_array_equal(l2, out_l2)
    assert np.shares_memory(l2, out_l2)
    assert_allclose(g1, g2)
    assert_allclose(g1, g3)
    assert_array_equal(g1, out_g1)
    assert np.shares_memory(g1, out_g1)
    assert_array_equal(g2, out_g2)
    assert np.shares_memory(g2, out_g2)
    assert_array_equal(g3, out_g3)
    assert np.shares_memory(g3, out_g3)

    if hasattr(loss, "gradient_proba"):
        assert loss.is_multiclass  # only for HalfMultinomialLoss
        out_g4 = np.empty_like(raw_prediction)
        out_proba = np.empty_like(raw_prediction)
        g4, proba = loss.gradient_proba(
            y_true=y_true,
            raw_prediction=raw_prediction,
            sample_weight=sample_weight,
            gradient_out=out_g4,
            proba_out=out_proba,
        )
        assert_allclose(g1, out_g4)
        assert_allclose(g1, g4)
        assert_allclose(proba, out_proba)
        assert_allclose(np.sum(proba, axis=1), 1, rtol=1e-11)