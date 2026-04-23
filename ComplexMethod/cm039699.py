def test_validation_functions_routing(func, extra_args):
    """Check that the respective cv method is properly dispatching the metadata
    to the consumer."""
    scorer_registry = _Registry()
    scorer = ConsumingScorer(registry=scorer_registry).set_score_request(
        sample_weight="score_weights", metadata="score_metadata"
    )
    splitter_registry = _Registry()
    splitter = ConsumingSplitter(registry=splitter_registry).set_split_request(
        groups="split_groups", metadata="split_metadata"
    )
    estimator_registry = _Registry()
    estimator = ConsumingClassifier(registry=estimator_registry).set_fit_request(
        sample_weight="fit_sample_weight", metadata="fit_metadata"
    )

    n_samples = _num_samples(X)
    rng = np.random.RandomState(0)
    score_weights = rng.rand(n_samples)
    score_metadata = rng.rand(n_samples)
    split_groups = rng.randint(0, 3, n_samples)
    split_metadata = rng.rand(n_samples)
    fit_sample_weight = rng.rand(n_samples)
    fit_metadata = rng.rand(n_samples)

    scoring_args = {
        cross_validate: dict(scoring=dict(my_scorer=scorer, accuracy="accuracy")),
        cross_val_score: dict(scoring=scorer),
        learning_curve: dict(scoring=scorer),
        validation_curve: dict(scoring=scorer),
        permutation_test_score: dict(scoring=scorer),
        cross_val_predict: dict(),
    }

    params = dict(
        split_groups=split_groups,
        split_metadata=split_metadata,
        fit_sample_weight=fit_sample_weight,
        fit_metadata=fit_metadata,
    )

    if func is not cross_val_predict:
        params.update(
            score_weights=score_weights,
            score_metadata=score_metadata,
        )

    func(
        estimator,
        X=X,
        y=y,
        cv=splitter,
        **scoring_args[func],
        **extra_args,
        params=params,
    )

    if func is not cross_val_predict:
        # cross_val_predict doesn't need a scorer
        assert len(scorer_registry)
    for _scorer in scorer_registry:
        check_recorded_metadata(
            obj=_scorer,
            method="score",
            parent=func.__name__,
            split_params=("sample_weight", "metadata"),
            sample_weight=score_weights,
            metadata=score_metadata,
        )

    assert len(splitter_registry)
    for _splitter in splitter_registry:
        check_recorded_metadata(
            obj=_splitter,
            method="split",
            parent=func.__name__,
            groups=split_groups,
            metadata=split_metadata,
        )

    assert len(estimator_registry)
    for _estimator in estimator_registry:
        check_recorded_metadata(
            obj=_estimator,
            method="fit",
            parent=func.__name__,
            split_params=("sample_weight", "metadata"),
            sample_weight=fit_sample_weight,
            metadata=fit_metadata,
        )