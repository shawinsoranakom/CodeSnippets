def test_loss_on_specific_values(
    loss, y_true, raw_prediction, loss_true, gradient_true, hessian_true
):
    """Test losses, gradients and hessians at specific values."""
    loss1 = loss(y_true=np.array([y_true]), raw_prediction=np.array([raw_prediction]))
    grad1 = loss.gradient(
        y_true=np.array([y_true]), raw_prediction=np.array([raw_prediction])
    )
    loss2, grad2 = loss.loss_gradient(
        y_true=np.array([y_true]), raw_prediction=np.array([raw_prediction])
    )
    grad3, hess = loss.gradient_hessian(
        y_true=np.array([y_true]), raw_prediction=np.array([raw_prediction])
    )

    assert loss1 == approx(loss_true, rel=1e-15, abs=1e-15)
    assert loss2 == approx(loss_true, rel=1e-15, abs=1e-15)

    if gradient_true is not None:
        assert grad1 == approx(gradient_true, rel=1e-15, abs=1e-15)
        assert grad2 == approx(gradient_true, rel=1e-15, abs=1e-15)
        assert grad3 == approx(gradient_true, rel=1e-15, abs=1e-15)

    if hessian_true is not None:
        assert hess == approx(hessian_true, rel=1e-15, abs=1e-15)