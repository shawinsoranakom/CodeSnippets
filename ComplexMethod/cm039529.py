def test_prediction_error_custom_artist(
    pyplot, regressor_fitted, class_method, scatter_kwargs, line_kwargs
):
    """Check that we can tune the style of the line and the scatter."""
    extra_params = {
        "kind": "actual_vs_predicted",
        "scatter_kwargs": scatter_kwargs,
        "line_kwargs": line_kwargs,
    }
    if class_method == "from_estimator":
        display = PredictionErrorDisplay.from_estimator(
            regressor_fitted, X, y, **extra_params
        )
    else:
        y_pred = regressor_fitted.predict(X)
        display = PredictionErrorDisplay.from_predictions(
            y_true=y, y_pred=y_pred, **extra_params
        )

    if line_kwargs is not None:
        assert display.line_.get_linestyle() == "-"
        assert display.line_.get_color() == "red"
    else:
        assert display.line_.get_linestyle() == "--"
        assert display.line_.get_color() == "black"
        assert display.line_.get_alpha() == 0.7

    if scatter_kwargs is not None:
        assert_allclose(display.scatter_.get_facecolor(), [[0.0, 0.0, 1.0, 0.9]])
        assert_allclose(display.scatter_.get_edgecolor(), [[0.0, 0.0, 1.0, 0.9]])
    else:
        assert display.scatter_.get_alpha() == 0.8