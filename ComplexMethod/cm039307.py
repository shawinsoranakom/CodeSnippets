def test_metadata_is_routed_correctly_to_scorer(metaestimator):
    """Test that any requested metadata is correctly routed to the underlying
    scorers in CV estimators.
    """
    if "scorer_name" not in metaestimator:
        # This test only makes sense for CV estimators
        return

    metaestimator_class = metaestimator["metaestimator"]
    routing_methods = metaestimator["scorer_routing_methods"]
    method_mapping = metaestimator.get("method_mapping", {})

    for method_name in routing_methods:
        kwargs, (estimator, _), (scorer, registry), (cv, _) = get_init_args(
            metaestimator, sub_estimator_consumes=True
        )
        scorer.set_score_request(sample_weight=True)
        if cv:
            cv.set_split_request(groups=True, metadata=True)
        if estimator is not None:
            set_requests(
                estimator,
                method_mapping=method_mapping,
                methods=[method_name],
                metadata_name="sample_weight",
            )
        instance = metaestimator_class(**kwargs)
        method = getattr(instance, method_name)
        method_kwargs = {"sample_weight": sample_weight}
        if "fit" not in method_name:
            instance.fit(X, y)
        method(X, y, **method_kwargs)

        assert registry
        for _scorer in registry:
            check_recorded_metadata(
                obj=_scorer,
                method="score",
                parent=method_name,
                split_params=("sample_weight",),
                **method_kwargs,
            )