def _yield_checks(estimator):
    name = estimator.__class__.__name__
    tags = get_tags(estimator)

    yield check_estimators_dtypes
    if has_fit_parameter(estimator, "sample_weight"):
        yield check_sample_weights_pandas_series
        yield check_sample_weights_not_an_array
        yield check_sample_weights_list
        yield check_all_zero_sample_weights_error
        if not tags.input_tags.pairwise:
            # We skip pairwise because the data is not pairwise
            yield check_sample_weights_shape
            yield check_sample_weights_not_overwritten
            yield check_sample_weight_equivalence_on_dense_data
            if tags.input_tags.sparse:
                yield check_sample_weight_equivalence_on_sparse_data

    # Check that all estimator yield informative messages when
    # trained on empty datasets
    if not tags.no_validation:
        yield check_complex_data
        yield check_dtype_object
        yield check_estimators_empty_data_messages

    if name not in CROSS_DECOMPOSITION:
        # cross-decomposition's "transform" returns X and Y
        yield check_pipeline_consistency

    if not tags.input_tags.allow_nan and not tags.no_validation:
        # Test that all estimators check their input for NaN's and infs
        yield check_estimators_nan_inf

    if tags.input_tags.pairwise:
        # Check that pairwise estimator throws error on non-square input
        yield check_nonsquare_error

    if hasattr(estimator, "sparsify"):
        yield check_sparsify_coefficients

    yield check_estimator_sparse_tag
    yield check_estimator_sparse_array
    yield check_estimator_sparse_matrix

    # Test that estimators can be pickled, and once pickled
    # give the same answer as before.
    yield check_estimators_pickle
    yield partial(check_estimators_pickle, readonly_memmap=True)

    for check in _yield_array_api_checks(
        estimator,
        only_numpy=not tags.array_api_support,
    ):
        yield check

    yield check_f_contiguous_array_estimator