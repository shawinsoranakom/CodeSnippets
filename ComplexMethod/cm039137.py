def _update_dict(
    dictionary,
    Y,
    code,
    A=None,
    B=None,
    verbose=False,
    random_state=None,
    positive=False,
):
    """Update the dense dictionary factor in place.

    Parameters
    ----------
    dictionary : ndarray of shape (n_components, n_features)
        Value of the dictionary at the previous iteration.

    Y : ndarray of shape (n_samples, n_features)
        Data matrix.

    code : ndarray of shape (n_samples, n_components)
        Sparse coding of the data against which to optimize the dictionary.

    A : ndarray of shape (n_components, n_components), default=None
        Together with `B`, sufficient stats of the online model to update the
        dictionary.

    B : ndarray of shape (n_features, n_components), default=None
        Together with `A`, sufficient stats of the online model to update the
        dictionary.

    verbose: bool, default=False
        Degree of output the procedure will print.

    random_state : int, RandomState instance or None, default=None
        Used for randomly initializing the dictionary. Pass an int for
        reproducible results across multiple function calls.
        See :term:`Glossary <random_state>`.

    positive : bool, default=False
        Whether to enforce positivity when finding the dictionary.

        .. versionadded:: 0.20
    """
    n_samples, n_components = code.shape
    random_state = check_random_state(random_state)

    if A is None:
        A = code.T @ code
    if B is None:
        B = Y.T @ code

    n_unused = 0

    for k in range(n_components):
        if A[k, k] > 1e-6:
            # 1e-6 is arbitrary but consistent with the spams implementation
            dictionary[k] += (B[:, k] - A[k] @ dictionary) / A[k, k]
        else:
            # kth atom is almost never used -> sample a new one from the data
            newd = Y[random_state.choice(n_samples)]

            # add small noise to avoid making the sparse coding ill conditioned
            noise_level = 0.01 * (newd.std() or 1)  # avoid 0 std
            noise = random_state.normal(0, noise_level, size=len(newd))

            dictionary[k] = newd + noise
            code[:, k] = 0
            n_unused += 1

        if positive:
            np.clip(dictionary[k], 0, None, out=dictionary[k])

        # Projection on the constraint set ||V_k|| <= 1
        dictionary[k] /= max(linalg.norm(dictionary[k]), 1)

    if verbose and n_unused > 0:
        print(f"{n_unused} unused atoms resampled.")