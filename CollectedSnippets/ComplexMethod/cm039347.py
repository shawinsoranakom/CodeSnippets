def _smacof_single(
    dissimilarities,
    metric=True,
    n_components=2,
    init=None,
    max_iter=300,
    verbose=0,
    eps=1e-6,
    random_state=None,
    normalized_stress=False,
):
    """Computes multidimensional scaling using SMACOF algorithm.

    Parameters
    ----------
    dissimilarities : ndarray of shape (n_samples, n_samples)
        Pairwise dissimilarities between the points. Must be symmetric.

    metric : bool, default=True
        Compute metric or nonmetric SMACOF algorithm.
        When ``False`` (i.e. non-metric MDS), dissimilarities with 0 are considered as
        missing values.

    n_components : int, default=2
        Number of dimensions in which to immerse the dissimilarities. If an
        ``init`` array is provided, this option is overridden and the shape of
        ``init`` is used to determine the dimensionality of the embedding
        space.

    init : ndarray of shape (n_samples, n_components), default=None
        Starting configuration of the embedding to initialize the algorithm. By
        default, the algorithm is initialized with a randomly chosen array.

    max_iter : int, default=300
        Maximum number of iterations of the SMACOF algorithm for a single run.

    verbose : int, default=0
        Level of verbosity.

    eps : float, default=1e-6
        The tolerance with respect to stress (normalized by the sum of squared
        embedding distances) at which to declare convergence.

        .. versionchanged:: 1.7
           The default value for `eps` has changed from 1e-3 to 1e-6, as a result
           of a bugfix in the computation of the convergence criterion.

    random_state : int, RandomState instance or None, default=None
        Determines the random number generator used to initialize the centers.
        Pass an int for reproducible results across multiple function calls.
        See :term:`Glossary <random_state>`.

    normalized_stress : bool, default=False
        Whether to return normalized stress value (Stress-1) instead of raw
        stress.

        .. versionadded:: 1.2

        .. versionchanged:: 1.7
           Normalized stress is now supported for metric MDS as well.

    Returns
    -------
    X : ndarray of shape (n_samples, n_components)
        Coordinates of the points in a ``n_components``-space.

    stress : float
        The final value of the stress (sum of squared distance of the
        disparities and the distances for all constrained points).
        If `normalized_stress=True`, returns Stress-1.
        A value of 0 indicates "perfect" fit, 0.025 excellent, 0.05 good,
        0.1 fair, and 0.2 poor [1]_.

    n_iter : int
        The number of iterations corresponding to the best stress.

    References
    ----------
    .. [1] "Nonmetric multidimensional scaling: a numerical method" Kruskal, J.
           Psychometrika, 29 (1964)

    .. [2] "Multidimensional scaling by optimizing goodness of fit to a nonmetric
           hypothesis" Kruskal, J. Psychometrika, 29, (1964)

    .. [3] "Modern Multidimensional Scaling - Theory and Applications" Borg, I.;
           Groenen P. Springer Series in Statistics (1997)
    """
    dissimilarities = check_symmetric(dissimilarities, raise_exception=True)

    n_samples = dissimilarities.shape[0]
    random_state = check_random_state(random_state)

    dissimilarities_flat = ((1 - np.tri(n_samples)) * dissimilarities).ravel()
    dissimilarities_flat_w = dissimilarities_flat[dissimilarities_flat != 0]
    if init is None:
        # Randomly choose initial configuration
        X = random_state.uniform(size=n_samples * n_components)
        X = X.reshape((n_samples, n_components))
    else:
        # overrides the parameter p
        n_components = init.shape[1]
        if n_samples != init.shape[0]:
            raise ValueError(
                "init matrix should be of shape (%d, %d)" % (n_samples, n_components)
            )
        X = init
    distances = euclidean_distances(X)

    # Out of bounds condition cannot happen because we are transforming
    # the training set here, but does sometimes get triggered in
    # practice due to machine precision issues. Hence "clip".
    ir = IsotonicRegression(out_of_bounds="clip")

    old_stress = None
    for it in range(max_iter):
        # Compute distance and monotonic regression
        if metric:
            disparities = dissimilarities
        else:
            distances_flat = distances.ravel()
            # dissimilarities with 0 are considered as missing values
            distances_flat_w = distances_flat[dissimilarities_flat != 0]

            # Compute the disparities using isotonic regression.
            # For the first SMACOF iteration, use scaled original dissimilarities.
            # (This choice follows the R implementation described in this paper:
            # https://www.jstatsoft.org/article/view/v102i10)
            if it < 1:
                disparities_flat = dissimilarities_flat_w
            else:
                disparities_flat = ir.fit_transform(
                    dissimilarities_flat_w, distances_flat_w
                )
            disparities = np.zeros_like(distances_flat)
            disparities[dissimilarities_flat != 0] = disparities_flat
            disparities = disparities.reshape((n_samples, n_samples))
            disparities *= np.sqrt(
                (n_samples * (n_samples - 1) / 2) / (disparities**2).sum()
            )
            disparities = disparities + disparities.T

        # Update X using the Guttman transform
        distances[distances == 0] = 1e-5
        ratio = disparities / distances
        B = -ratio
        B[np.arange(len(B)), np.arange(len(B))] += ratio.sum(axis=1)
        X = 1.0 / n_samples * np.dot(B, X)

        # Compute stress
        distances = euclidean_distances(X)
        stress = ((distances.ravel() - disparities.ravel()) ** 2).sum() / 2

        if verbose >= 2:  # pragma: no cover
            print(f"Iteration {it}, stress {stress:.4f}")
        if old_stress is not None:
            sum_squared_distances = (distances.ravel() ** 2).sum()
            if ((old_stress - stress) / (sum_squared_distances / 2)) < eps:
                if verbose:  # pragma: no cover
                    print(f"Convergence criterion reached (iteration {it}).")
                break
        old_stress = stress

    if normalized_stress:
        sum_squared_distances = (distances.ravel() ** 2).sum()
        stress = np.sqrt(stress / (sum_squared_distances / 2))

    return X, stress, it + 1