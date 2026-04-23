def test_predict_proba(loss, global_random_seed):
    """Test that predict_proba and gradient_proba work as expected."""
    n_samples = 20
    y_true, raw_prediction = random_y_true_raw_prediction(
        loss=loss,
        n_samples=n_samples,
        y_bound=(-100, 100),
        raw_bound=(-5, 5),
        seed=global_random_seed,
    )

    if hasattr(loss, "predict_proba"):
        proba = loss.predict_proba(raw_prediction)
        assert proba.shape == (n_samples, loss.n_classes)
        assert np.sum(proba, axis=1) == approx(1, rel=1e-11)

    if hasattr(loss, "gradient_proba"):
        for grad, proba in (
            (None, None),
            (None, np.empty_like(raw_prediction)),
            (np.empty_like(raw_prediction), None),
            (np.empty_like(raw_prediction), np.empty_like(raw_prediction)),
        ):
            grad, proba = loss.gradient_proba(
                y_true=y_true,
                raw_prediction=raw_prediction,
                sample_weight=None,
                gradient_out=grad,
                proba_out=proba,
            )
            assert proba.shape == (n_samples, loss.n_classes)
            assert np.sum(proba, axis=1) == approx(1, rel=1e-11)
            assert_allclose(
                grad,
                loss.gradient(
                    y_true=y_true,
                    raw_prediction=raw_prediction,
                    sample_weight=None,
                    gradient_out=None,
                ),
            )