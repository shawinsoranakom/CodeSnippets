def test_fit_docstring_attributes(name, Estimator):
    pytest.importorskip("numpydoc")
    from numpydoc import docscrape

    doc = docscrape.ClassDoc(Estimator)
    attributes = doc["Attributes"]

    if Estimator.__name__ in (
        "HalvingRandomSearchCV",
        "RandomizedSearchCV",
        "HalvingGridSearchCV",
        "GridSearchCV",
    ):
        est = _construct_searchcv_instance(Estimator)
    elif Estimator.__name__ in (
        "ColumnTransformer",
        "Pipeline",
        "FeatureUnion",
    ):
        est = _construct_compose_pipeline_instance(Estimator)
    elif Estimator.__name__ == "SparseCoder":
        est = _construct_sparse_coder(Estimator)
    elif Estimator.__name__ == "FrozenEstimator":
        X, y = make_classification(n_samples=20, n_features=5, random_state=0)
        est = Estimator(LogisticRegression().fit(X, y))
    else:
        # TODO(devtools): use _tested_estimators instead of all_estimators in the
        # decorator
        est = next(_construct_instances(Estimator))

    if Estimator.__name__ == "SelectKBest":
        est.set_params(k=2)
    elif Estimator.__name__ == "DummyClassifier":
        est.set_params(strategy="stratified")
    elif Estimator.__name__ == "CCA" or Estimator.__name__.startswith("PLS"):
        # default = 2 is invalid for single target
        est.set_params(n_components=1)
    elif Estimator.__name__ in (
        "GaussianRandomProjection",
        "SparseRandomProjection",
    ):
        # default="auto" raises an error with the shape of `X`
        est.set_params(n_components=2)
    elif Estimator.__name__ == "TSNE":
        # default raises an error, perplexity must be less than n_samples
        est.set_params(perplexity=2)
    # TODO(1.10) remove
    elif Estimator.__name__ == "MDS":
        # default raises a FutureWarning
        est.set_params(n_init=1, init="random")
    # TODO(1.10) remove l1_ratios
    # TODO(1.11) remove completely
    elif Estimator.__name__ == "LogisticRegressionCV":
        # default 'l1_ratios' value creates a FutureWarning
        # default 'scoring' value creates a FutureWarning
        est.set_params(l1_ratios=(0,), scoring="neg_log_loss")

    # Low max iter to speed up tests: we are only interested in checking the existence
    # of fitted attributes. This should be invariant to whether it has converged or not.
    if "max_iter" in est.get_params():
        est.set_params(max_iter=2)
        # min value for `TSNE` is 250
        if Estimator.__name__ == "TSNE":
            est.set_params(max_iter=250)

    if "random_state" in est.get_params():
        est.set_params(random_state=0)

    # In case we want to deprecate some attributes in the future
    skipped_attributes = {}

    if Estimator.__name__.endswith("Vectorizer"):
        # Vectorizer require some specific input data
        if Estimator.__name__ in (
            "CountVectorizer",
            "HashingVectorizer",
            "TfidfVectorizer",
        ):
            X = [
                "This is the first document.",
                "This document is the second document.",
                "And this is the third one.",
                "Is this the first document?",
            ]
        elif Estimator.__name__ == "DictVectorizer":
            X = [{"foo": 1, "bar": 2}, {"foo": 3, "baz": 1}]
        y = None
    else:
        X, y = make_classification(
            n_samples=20,
            n_features=3,
            n_redundant=0,
            n_classes=2,
            random_state=2,
        )

        y = _enforce_estimator_tags_y(est, y)
        X = _enforce_estimator_tags_X(est, X)

    if est.__sklearn_tags__().target_tags.one_d_labels:
        est.fit(y)
    elif est.__sklearn_tags__().target_tags.two_d_labels:
        est.fit(np.c_[y, y])
    elif est.__sklearn_tags__().input_tags.three_d_array:
        est.fit(X[np.newaxis, ...], y)
    else:
        est.fit(X, y)

    for attr in attributes:
        if attr.name in skipped_attributes:
            continue
        desc = " ".join(attr.desc).lower()
        # As certain attributes are present "only" if a certain parameter is
        # provided, this checks if the word "only" is present in the attribute
        # description, and if not the attribute is required to be present.
        if "only " in desc:
            continue
        # ignore deprecation warnings
        with ignore_warnings(category=FutureWarning):
            assert hasattr(est, attr.name)

    fit_attr = _get_all_fitted_attributes(est)
    fit_attr_names = [attr.name for attr in attributes]
    undocumented_attrs = set(fit_attr).difference(fit_attr_names)
    undocumented_attrs = set(undocumented_attrs).difference(skipped_attributes)
    if undocumented_attrs:
        raise AssertionError(
            f"Undocumented attributes for {Estimator.__name__}: {undocumented_attrs}"
        )