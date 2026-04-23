def _yield_all_checks(estimator, legacy: bool):
    name = estimator.__class__.__name__
    tags = get_tags(estimator)
    if not tags.input_tags.two_d_array:
        warnings.warn(
            "Can't test estimator {} which requires input  of type {}".format(
                name, tags.input_tags
            ),
            SkipTestWarning,
        )
        return
    if tags._skip_test:
        warnings.warn(
            "Explicit SKIP via _skip_test tag for estimator {}.".format(name),
            SkipTestWarning,
        )
        return

    for check in _yield_api_checks(estimator):
        yield check

    if not legacy:
        return  # pragma: no cover

    for check in _yield_checks(estimator):
        yield check
    if is_classifier(estimator):
        for check in _yield_classifier_checks(estimator):
            yield check
    if is_regressor(estimator):
        for check in _yield_regressor_checks(estimator):
            yield check
    if hasattr(estimator, "transform"):
        for check in _yield_transformer_checks(estimator):
            yield check
    if isinstance(estimator, ClusterMixin):
        for check in _yield_clustering_checks(estimator):
            yield check
    if is_outlier_detector(estimator):
        for check in _yield_outliers_checks(estimator):
            yield check
    yield check_parameters_default_constructible
    if not tags.non_deterministic:
        yield check_methods_sample_order_invariance
        yield check_methods_subset_invariance
    yield check_fit2d_1sample
    yield check_fit2d_1feature
    yield check_get_params_invariance
    yield check_set_params
    yield check_dict_unchanged
    yield check_fit_idempotent
    yield check_fit_check_is_fitted
    if not tags.no_validation:
        yield check_n_features_in
        yield check_fit1d
        yield check_fit2d_predict1d
        if tags.target_tags.required:
            yield check_requires_y_none
    if tags.input_tags.positive_only:
        yield check_fit_non_negative