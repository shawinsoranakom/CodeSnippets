def test_multiclass_colors_cmap(
    pyplot,
    n_classes,
    response_method,
    plot_method,
    multiclass_colors,
):
    """Check correct cmap used for all `multiclass_colors` inputs."""
    import matplotlib as mpl

    X, y = make_blobs(n_samples=150, centers=n_classes, n_features=2, random_state=42)
    clf = LogisticRegression().fit(X, y)

    disp = DecisionBoundaryDisplay.from_estimator(
        clf,
        X,
        response_method=response_method,
        plot_method=plot_method,
        multiclass_colors=multiclass_colors,
    )

    # Non-regression test for PR #33651
    assert isinstance(disp.multiclass_colors_, np.ndarray)

    if multiclass_colors is None:
        # Make sure the correct colors are selected from the corresponding petroff color
        # sequences or "gist_rainbow"
        if len(clf.classes_) == 3:
            multiclass_colors = PETROFF_COLORS[:3]
        else:
            multiclass_colors = "gist_rainbow"

    if isinstance(multiclass_colors, str):
        cmap = pyplot.get_cmap(multiclass_colors)
        colors = cmap(np.linspace(0, 1, len(clf.classes_)))
    else:
        colors = mpl.colors.to_rgba_array(multiclass_colors)

    # Make sure the colormap has enough distinct colors.
    assert disp.n_classes == len(np.unique(colors, axis=0))

    if response_method == "predict":
        if plot_method == "contour":
            assert disp.surface_.colors == "black"
        else:
            cmap = mpl.colors.ListedColormap(colors)
            assert disp.surface_.cmap == cmap

    else:
        if plot_method == "contour":
            # the last display additionally contains the class boundary contours
            assert disp.surface_[-1].colors == "black"
            del disp.surface_[-1]
        cmaps = [
            mpl.colors.LinearSegmentedColormap.from_list(
                f"colormap_{class_idx}", [(1.0, 1.0, 1.0, 1.0), (r, g, b, 1.0)]
            )
            for class_idx, (r, g, b, _) in enumerate(colors)
        ]
        # Make sure every class has its own surface.
        assert len(disp.surface_) == disp.n_classes

        for idx, quad in enumerate(disp.surface_):
            assert quad.cmap == cmaps[idx]