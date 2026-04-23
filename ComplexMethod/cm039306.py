def test_setting_request_on_sub_estimator_removes_error(metaestimator):
    # When the metadata is explicitly requested on the sub-estimator, there
    # should be no errors.
    if "estimator" not in metaestimator:
        # This test only makes sense for metaestimators which have a
        # sub-estimator, e.g. MyMetaEstimator(estimator=MySubEstimator())
        return

    metaestimator_class = metaestimator["metaestimator"]
    X = metaestimator["X"]
    y = metaestimator["y"]
    routing_methods = filter_metadata_in_routing_methods(
        metaestimator["estimator_routing_methods"]
    )
    method_mapping = metaestimator.get("method_mapping", {})
    preserves_metadata = metaestimator.get("preserves_metadata", True)

    for method_name, metadata_keys in routing_methods.items():
        for key in metadata_keys:
            val = {"sample_weight": sample_weight, "metadata": metadata}[key]
            method_kwargs = {key: val}

            kwargs, (estimator, registry), (scorer, _), (cv, _) = get_init_args(
                metaestimator, sub_estimator_consumes=True
            )
            if scorer:
                set_requests(
                    scorer, method_mapping={}, methods=["score"], metadata_name=key
                )
            if cv:
                cv.set_split_request(groups=True, metadata=True)

            # `set_{method}_request({metadata}==True)` on the underlying objects
            set_requests(
                estimator,
                method_mapping=method_mapping,
                methods=[method_name],
                metadata_name=key,
            )

            instance = metaestimator_class(**kwargs)
            method = getattr(instance, method_name)
            extra_method_args = metaestimator.get("method_args", {}).get(
                method_name, {}
            )
            if "fit" not in method_name:
                # fit before calling method
                instance.fit(X, y)
            try:
                # `fit` and `partial_fit` accept y, others don't.
                method(X, y, **method_kwargs, **extra_method_args)
            except TypeError:
                method(X, **method_kwargs, **extra_method_args)

            # sanity check that registry is not empty, or else the test passes
            # trivially
            assert registry
            split_params = (
                method_kwargs.keys() if preserves_metadata == "subset" else ()
            )
            for estimator in registry:
                check_recorded_metadata(
                    estimator,
                    method=method_name,
                    parent=method_name,
                    split_params=split_params,
                    **method_kwargs,
                )