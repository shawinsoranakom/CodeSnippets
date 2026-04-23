def test_splitting_missing_values(
    X_binned,
    all_gradients,
    has_missing_values,
    n_bins_non_missing,
    expected_split_on_nan,
    expected_bin_idx,
    expected_go_to_left,
):
    # Make sure missing values are properly supported.
    # we build an artificial example with gradients such that the best split
    # is on bin_idx=3, when there are no missing values.
    # Then we introduce missing values and:
    #   - make sure the chosen bin is correct (find_best_bin()): it's
    #     still the same split, even though the index of the bin may change
    #   - make sure the missing values are mapped to the correct child
    #     (split_indices())

    n_bins = max(X_binned) + 1
    n_samples = len(X_binned)
    l2_regularization = 0.0
    min_hessian_to_split = 1e-3
    min_samples_leaf = 1
    min_gain_to_split = 0.0

    sample_indices = np.arange(n_samples, dtype=np.uint32)
    X_binned = np.array(X_binned, dtype=X_BINNED_DTYPE).reshape(-1, 1)
    X_binned = np.asfortranarray(X_binned)
    all_gradients = np.array(all_gradients, dtype=G_H_DTYPE)
    has_missing_values = np.array([has_missing_values], dtype=np.uint8)
    all_hessians = np.ones(1, dtype=G_H_DTYPE)
    sum_gradients = all_gradients.sum()
    sum_hessians = 1 * n_samples
    hessians_are_constant = True

    builder = HistogramBuilder(
        X_binned, n_bins, all_gradients, all_hessians, hessians_are_constant, n_threads
    )

    n_bins_non_missing = np.array([n_bins_non_missing], dtype=np.uint32)
    monotonic_cst = np.array(
        [MonotonicConstraint.NO_CST] * X_binned.shape[1], dtype=np.int8
    )
    is_categorical = np.zeros_like(monotonic_cst, dtype=np.uint8)
    missing_values_bin_idx = n_bins - 1
    splitter = Splitter(
        X_binned,
        n_bins_non_missing,
        missing_values_bin_idx,
        has_missing_values,
        is_categorical,
        monotonic_cst,
        l2_regularization,
        min_hessian_to_split,
        min_samples_leaf,
        min_gain_to_split,
        hessians_are_constant,
    )

    histograms = builder.compute_histograms_brute(sample_indices)
    value = compute_node_value(
        sum_gradients, sum_hessians, -np.inf, np.inf, l2_regularization
    )
    split_info = splitter.find_node_split(
        n_samples, histograms, sum_gradients, sum_hessians, value
    )

    assert split_info.bin_idx == expected_bin_idx
    if has_missing_values:
        assert split_info.missing_go_to_left == expected_go_to_left

    split_on_nan = split_info.bin_idx == n_bins_non_missing[0] - 1
    assert split_on_nan == expected_split_on_nan

    # Make sure the split is properly computed.
    # This also make sure missing values are properly assigned to the correct
    # child in split_indices()
    samples_left, samples_right, _ = splitter.split_indices(
        split_info, splitter.partition
    )

    if not expected_split_on_nan:
        # When we don't split on nans, the split should always be the same.
        assert set(samples_left) == set([0, 1, 2, 3])
        assert set(samples_right) == set([4, 5, 6, 7, 8, 9])
    else:
        # When we split on nans, samples with missing values are always mapped
        # to the right child.
        missing_samples_indices = np.flatnonzero(
            np.array(X_binned) == missing_values_bin_idx
        )
        non_missing_samples_indices = np.flatnonzero(
            np.array(X_binned) != missing_values_bin_idx
        )

        assert set(samples_right) == set(missing_samples_indices)
        assert set(samples_left) == set(non_missing_samples_indices)