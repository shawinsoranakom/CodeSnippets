def fast_mcd(
    X,
    support_fraction=None,
    cov_computation_method=empirical_covariance,
    random_state=None,
):
    """Estimate the Minimum Covariance Determinant matrix.

    Read more in the :ref:`User Guide <robust_covariance>`.

    Parameters
    ----------
    X : array-like of shape (n_samples, n_features)
        The data matrix, with p features and n samples.

    support_fraction : float, default=None
        The proportion of points to be included in the support of the raw
        MCD estimate. Default is `None`, which implies that the minimum
        value of `support_fraction` will be used within the algorithm:
        `(n_samples + n_features + 1) / 2 * n_samples`. This parameter must be
        in the range (0, 1).

    cov_computation_method : callable, \
            default=:func:`sklearn.covariance.empirical_covariance`
        The function which will be used to compute the covariance.
        Must return an array of shape (n_features, n_features).

    random_state : int, RandomState instance or None, default=None
        Determines the pseudo random number generator for shuffling the data.
        Pass an int for reproducible results across multiple function calls.
        See :term:`Glossary <random_state>`.

    Returns
    -------
    location : ndarray of shape (n_features,)
        Robust location of the data.

    covariance : ndarray of shape (n_features, n_features)
        Robust covariance of the features.

    support : ndarray of shape (n_samples,), dtype=bool
        A mask of the observations that have been used to compute
        the robust location and covariance estimates of the data set.

    Notes
    -----
    The FastMCD algorithm has been introduced by Rousseuw and Van Driessen
    in "A Fast Algorithm for the Minimum Covariance Determinant Estimator,
    1999, American Statistical Association and the American Society
    for Quality, TECHNOMETRICS".
    The principle is to compute robust estimates and random subsets before
    pooling them into a larger subsets, and finally into the full data set.
    Depending on the size of the initial sample, we have one, two or three
    such computation levels.

    Note that only raw estimates are returned. If one is interested in
    the correction and reweighting steps described in [RouseeuwVan]_,
    see the MinCovDet object.

    References
    ----------

    .. [RouseeuwVan] A Fast Algorithm for the Minimum Covariance
        Determinant Estimator, 1999, American Statistical Association
        and the American Society for Quality, TECHNOMETRICS

    .. [Butler1993] R. W. Butler, P. L. Davies and M. Jhun,
        Asymptotics For The Minimum Covariance Determinant Estimator,
        The Annals of Statistics, 1993, Vol. 21, No. 3, 1385-1400
    """
    random_state = check_random_state(random_state)

    X = check_array(X, ensure_min_samples=2, estimator="fast_mcd")
    n_samples, n_features = X.shape

    # minimum breakdown value
    if support_fraction is None:
        n_support = min(int(np.ceil(0.5 * (n_samples + n_features + 1))), n_samples)
    else:
        n_support = int(support_fraction * n_samples)

    # 1-dimensional case quick computation
    # (Rousseeuw, P. J. and Leroy, A. M. (2005) References, in Robust
    #  Regression and Outlier Detection, John Wiley & Sons, chapter 4)
    if n_features == 1:
        if n_support < n_samples:
            # find the sample shortest halves
            X_sorted = np.sort(np.ravel(X))
            diff = X_sorted[n_support:] - X_sorted[: (n_samples - n_support)]
            halves_start = np.where(diff == np.min(diff))[0]
            # take the middle points' mean to get the robust location estimate
            location = (
                0.5
                * (X_sorted[n_support + halves_start] + X_sorted[halves_start]).mean()
            )
            support = np.zeros(n_samples, dtype=bool)
            X_centered = X - location
            support[np.argsort(np.abs(X_centered), 0)[:n_support]] = True
            covariance = np.asarray([[np.var(X[support])]])
            location = np.array([location])
            # get precision matrix in an optimized way
            precision = linalg.pinvh(covariance)
            dist = (np.dot(X_centered, precision) * (X_centered)).sum(axis=1)
        else:
            support = np.ones(n_samples, dtype=bool)
            covariance = np.asarray([[np.var(X)]])
            location = np.asarray([np.mean(X)])
            X_centered = X - location
            # get precision matrix in an optimized way
            precision = linalg.pinvh(covariance)
            dist = (np.dot(X_centered, precision) * (X_centered)).sum(axis=1)
    # Starting FastMCD algorithm for p-dimensional case
    if (n_samples > 500) and (n_features > 1):
        # 1. Find candidate supports on subsets
        # a. split the set in subsets of size ~ 300
        n_subsets = n_samples // 300
        n_samples_subsets = n_samples // n_subsets
        samples_shuffle = random_state.permutation(n_samples)
        h_subset = int(np.ceil(n_samples_subsets * (n_support / float(n_samples))))
        # b. perform a total of 500 trials
        n_trials_tot = 500
        # c. select 10 best (location, covariance) for each subset
        n_best_sub = 10
        n_trials = max(10, n_trials_tot // n_subsets)
        n_best_tot = n_subsets * n_best_sub
        all_best_locations = np.zeros((n_best_tot, n_features))
        try:
            all_best_covariances = np.zeros((n_best_tot, n_features, n_features))
        except MemoryError:
            # The above is too big. Let's try with something much small
            # (and less optimal)
            n_best_tot = 10
            all_best_covariances = np.zeros((n_best_tot, n_features, n_features))
            n_best_sub = 2
        for i in range(n_subsets):
            low_bound = i * n_samples_subsets
            high_bound = low_bound + n_samples_subsets
            current_subset = X[samples_shuffle[low_bound:high_bound]]
            best_locations_sub, best_covariances_sub, _, _ = select_candidates(
                current_subset,
                h_subset,
                n_trials,
                select=n_best_sub,
                n_iter=2,
                cov_computation_method=cov_computation_method,
                random_state=random_state,
            )
            subset_slice = np.arange(i * n_best_sub, (i + 1) * n_best_sub)
            all_best_locations[subset_slice] = best_locations_sub
            all_best_covariances[subset_slice] = best_covariances_sub
        # 2. Pool the candidate supports into a merged set
        # (possibly the full dataset)
        n_samples_merged = min(1500, n_samples)
        h_merged = int(np.ceil(n_samples_merged * (n_support / float(n_samples))))
        if n_samples > 1500:
            n_best_merged = 10
        else:
            n_best_merged = 1
        # find the best couples (location, covariance) on the merged set
        selection = random_state.permutation(n_samples)[:n_samples_merged]
        locations_merged, covariances_merged, supports_merged, d = select_candidates(
            X[selection],
            h_merged,
            n_trials=(all_best_locations, all_best_covariances),
            select=n_best_merged,
            cov_computation_method=cov_computation_method,
            random_state=random_state,
        )
        # 3. Finally get the overall best (locations, covariance) couple
        if n_samples < 1500:
            # directly get the best couple (location, covariance)
            location = locations_merged[0]
            covariance = covariances_merged[0]
            support = np.zeros(n_samples, dtype=bool)
            dist = np.zeros(n_samples)
            support[selection] = supports_merged[0]
            dist[selection] = d[0]
        else:
            # select the best couple on the full dataset
            locations_full, covariances_full, supports_full, d = select_candidates(
                X,
                n_support,
                n_trials=(locations_merged, covariances_merged),
                select=1,
                cov_computation_method=cov_computation_method,
                random_state=random_state,
            )
            location = locations_full[0]
            covariance = covariances_full[0]
            support = supports_full[0]
            dist = d[0]
    elif n_features > 1:
        # 1. Find the 10 best couples (location, covariance)
        # considering two iterations
        n_trials = 30
        n_best = 10
        locations_best, covariances_best, _, _ = select_candidates(
            X,
            n_support,
            n_trials=n_trials,
            select=n_best,
            n_iter=2,
            cov_computation_method=cov_computation_method,
            random_state=random_state,
        )
        # 2. Select the best couple on the full dataset amongst the 10
        locations_full, covariances_full, supports_full, d = select_candidates(
            X,
            n_support,
            n_trials=(locations_best, covariances_best),
            select=1,
            cov_computation_method=cov_computation_method,
            random_state=random_state,
        )
        location = locations_full[0]
        covariance = covariances_full[0]
        support = supports_full[0]
        dist = d[0]

    return location, covariance, support, dist