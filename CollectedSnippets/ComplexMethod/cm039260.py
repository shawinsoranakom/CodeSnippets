def test_decision_boundary_display_regressor(pyplot, response_method, plot_method):
    """Check that we can display the decision boundary for a regressor."""
    X, y = load_diabetes(return_X_y=True)
    X = X[:, :2]
    tree = DecisionTreeRegressor().fit(X, y)
    fig, ax = pyplot.subplots()
    eps = 2.0
    disp = DecisionBoundaryDisplay.from_estimator(
        tree,
        X,
        response_method=response_method,
        ax=ax,
        eps=eps,
        plot_method=plot_method,
    )
    if disp.n_classes == 2 or plot_method == "contour":
        assert isinstance(disp.surface_, pyplot.matplotlib.contour.QuadContourSet)
    else:
        assert isinstance(disp.surface_, list)
        for surface in disp.surface_:
            assert isinstance(surface, pyplot.matplotlib.contour.QuadContourSet)
    assert disp.ax_ == ax
    assert disp.figure_ == fig

    x0, x1 = X[:, 0], X[:, 1]

    x0_min, x0_max = x0.min() - eps, x0.max() + eps
    x1_min, x1_max = x1.min() - eps, x1.max() + eps

    assert disp.xx0.min() == pytest.approx(x0_min)
    assert disp.xx0.max() == pytest.approx(x0_max)
    assert disp.xx1.min() == pytest.approx(x1_min)
    assert disp.xx1.max() == pytest.approx(x1_max)

    fig2, ax2 = pyplot.subplots()
    # change plotting method for second plot
    disp.plot(plot_method="pcolormesh", ax=ax2, shading="auto")
    assert isinstance(disp.surface_, pyplot.matplotlib.collections.QuadMesh)
    assert disp.ax_ == ax2
    assert disp.figure_ == fig2