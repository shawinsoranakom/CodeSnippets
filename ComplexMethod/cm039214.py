def test_make_classification_return_x_y():
    """
    Test that make_classification returns a Bunch when return_X_y is False.

    Also that bunch.X is the same as X
    """

    kwargs = {
        "n_samples": 100,
        "n_features": 20,
        "n_informative": 5,
        "n_redundant": 1,
        "n_repeated": 1,
        "n_classes": 3,
        "n_clusters_per_class": 2,
        "weights": None,
        "flip_y": 0.01,
        "class_sep": 1.0,
        "hypercube": True,
        "shift": 0.0,
        "scale": 1.0,
        "shuffle": True,
        "random_state": 42,
        "return_X_y": True,
    }

    X, y = make_classification(**kwargs)

    kwargs["return_X_y"] = False
    bunch = make_classification(**kwargs)

    assert (
        hasattr(bunch, "DESCR")
        and hasattr(bunch, "parameters")
        and hasattr(bunch, "feature_info")
        and hasattr(bunch, "X")
        and hasattr(bunch, "y")
    )

    def count(str_):
        return bunch.feature_info.count(str_)

    assert np.array_equal(X, bunch.X)
    assert np.array_equal(y, bunch.y)
    assert bunch.DESCR == make_classification.__doc__
    assert bunch.parameters == kwargs
    assert count("informative") == kwargs["n_informative"]
    assert count("redundant") == kwargs["n_redundant"]
    assert count("repeated") == kwargs["n_repeated"]