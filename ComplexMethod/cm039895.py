def check_dont_overwrite_parameters(name, estimator_orig):
    # check that fit method only changes or sets private attributes
    estimator = clone(estimator_orig)
    rnd = np.random.RandomState(0)
    X = 3 * rnd.uniform(size=(20, 3))
    X = _enforce_estimator_tags_X(estimator_orig, X)
    y = X[:, 0].astype(int)
    y = _enforce_estimator_tags_y(estimator, y)

    if hasattr(estimator, "n_components"):
        estimator.n_components = 1
    if hasattr(estimator, "n_clusters"):
        estimator.n_clusters = 1

    set_random_state(estimator, 1)
    dict_before_fit = estimator.__dict__.copy()
    estimator.fit(X, y)

    dict_after_fit = estimator.__dict__

    public_keys_after_fit = [
        key for key in dict_after_fit.keys() if _is_public_parameter(key)
    ]

    attrs_added_by_fit = [
        key for key in public_keys_after_fit if key not in dict_before_fit.keys()
    ]

    # check that fit doesn't add any public attribute
    assert not attrs_added_by_fit, (
        "Estimator adds public attribute(s) during"
        " the fit method."
        " Estimators are only allowed to add private attributes"
        " either started with _ or ended"
        " with _ but %s added" % ", ".join(attrs_added_by_fit)
    )

    # check that fit doesn't change any public attribute
    attrs_changed_by_fit = [
        key
        for key in public_keys_after_fit
        if (dict_before_fit[key] is not dict_after_fit[key])
    ]

    assert not attrs_changed_by_fit, (
        "Estimator changes public attribute(s) during"
        " the fit method. Estimators are only allowed"
        " to change attributes started"
        " or ended with _, but"
        " %s changed" % ", ".join(attrs_changed_by_fit)
    )