def test_zorder(pyplot, response_method, plot_method):
    """Check that decision boundaries are plotted in the background."""
    X = np.array([[-1, -1], [-2, -1], [1, 1], [2, 1], [2, 2], [3, 2]])
    y = np.arange(6)
    clf = LogisticRegression().fit(X, y)
    disp = DecisionBoundaryDisplay.from_estimator(
        clf, X, response_method=response_method, plot_method=plot_method
    )
    # TODO: Remove version check and the else branch once 3.10 is the minimal
    # supported matplotlib version.
    import matplotlib as mpl

    # disp.surface_ is QuadContourSet or QuadMesh (for "pcolormesh"). In matplotlib
    # 3.10.0, the API for QuadContourSet was changed to produce only one collection
    # per plot (as it was and is the case for QuadMesh) and `.collections` was
    # deprecated, whereas before, a collection was created for each level
    # separately.
    if (
        parse_version(mpl.__version__) >= parse_version("3.10.0")
        or plot_method == "pcolormesh"
    ):
        if isinstance(disp.surface_, list):
            for surface in disp.surface_:
                assert surface.get_zorder() == -1
        else:
            assert disp.surface_.get_zorder() == -1
    else:
        if isinstance(disp.surface_, list):
            for surface in disp.surface_:
                for collection in surface.collections:
                    assert collection.get_zorder() == -1
        else:
            for collection in disp.surface_.collections:
                assert collection.get_zorder() == -1