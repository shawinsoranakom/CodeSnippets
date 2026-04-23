def _parallel_build_estimators(
    n_estimators,
    ensemble,
    X,
    y,
    sample_weight,
    seeds,
    total_n_estimators,
    verbose,
    check_input,
    fit_params,
):
    """Private function used to build a batch of estimators within a job."""
    # Retrieve settings
    n_samples, n_features = X.shape
    max_features = ensemble._max_features
    max_samples = ensemble._max_samples
    bootstrap = ensemble.bootstrap
    bootstrap_features = ensemble.bootstrap_features
    has_check_input = has_fit_parameter(ensemble.estimator_, "check_input")
    requires_feature_indexing = bootstrap_features or max_features != n_features
    consumes_sample_weight = _consumes_sample_weight(ensemble.estimator_)

    # Build estimators
    estimators = []
    estimators_features = []

    for i in range(n_estimators):
        if verbose > 1:
            print(
                "Building estimator %d of %d for this parallel run (total %d)..."
                % (i + 1, n_estimators, total_n_estimators)
            )

        random_state = seeds[i]
        estimator = ensemble._make_estimator(append=False, random_state=random_state)

        if has_check_input:
            estimator_fit = partial(estimator.fit, check_input=check_input)
        else:
            estimator_fit = estimator.fit

        # Draw random feature, sample indices (using normalized sample_weight
        # as probabilities if provided).
        features, indices = _generate_bagging_indices(
            random_state,
            bootstrap_features,
            bootstrap,
            n_features,
            n_samples,
            max_features,
            max_samples,
            sample_weight,
        )

        fit_params_ = fit_params.copy()

        # Note: Row sampling can be achieved either through setting sample_weight or
        # by indexing. The former is more memory efficient. Therefore, use this method
        # if possible, otherwise use indexing.
        if consumes_sample_weight:
            # Row sampling by setting sample_weight
            indices_as_sample_weight = np.bincount(indices, minlength=n_samples)
            fit_params_["sample_weight"] = indices_as_sample_weight
            X_ = X[:, features] if requires_feature_indexing else X
            estimator_fit(X_, y, **fit_params_)
        else:
            # Row sampling by indexing
            y_ = _safe_indexing(y, indices)
            X_ = _safe_indexing(X, indices)
            fit_params_ = _check_method_params(X, params=fit_params_, indices=indices)
            if requires_feature_indexing:
                X_ = X_[:, features]
            estimator_fit(X_, y_, **fit_params_)

        estimators.append(estimator)
        estimators_features.append(features)

    return estimators, estimators_features