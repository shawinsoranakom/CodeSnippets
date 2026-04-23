def _dict_learning(
    X,
    n_components,
    *,
    alpha,
    max_iter,
    tol,
    method,
    n_jobs,
    dict_init,
    code_init,
    callback,
    verbose,
    random_state,
    return_n_iter,
    positive_dict,
    positive_code,
    method_max_iter,
):
    """Main dictionary learning algorithm"""
    t0 = time.time()
    # Init the code and the dictionary with SVD of Y
    if code_init is not None and dict_init is not None:
        code = np.array(code_init, order="F")
        # Don't copy V, it will happen below
        dictionary = dict_init
    else:
        code, S, dictionary = linalg.svd(X, full_matrices=False)
        # flip the initial code's sign to enforce deterministic output
        code, dictionary = svd_flip(code, dictionary)
        dictionary = S[:, np.newaxis] * dictionary
    r = len(dictionary)
    if n_components <= r:  # True even if n_components=None
        code = code[:, :n_components]
        dictionary = dictionary[:n_components, :]
    else:
        code = np.c_[code, np.zeros((len(code), n_components - r))]
        dictionary = np.r_[
            dictionary, np.zeros((n_components - r, dictionary.shape[1]))
        ]

    # Fortran-order dict better suited for the sparse coding which is the
    # bottleneck of this algorithm.
    dictionary = np.asfortranarray(dictionary)

    errors = []
    current_cost = np.nan

    if verbose == 1:
        print("[dict_learning]", end=" ")

    # If max_iter is 0, number of iterations returned should be zero
    ii = -1

    for ii in range(max_iter):
        dt = time.time() - t0
        if verbose == 1:
            sys.stdout.write(".")
            sys.stdout.flush()
        elif verbose:
            print(
                "Iteration % 3i (elapsed time: % 3is, % 4.1fmn, current cost % 7.3f)"
                % (ii, dt, dt / 60, current_cost)
            )

        # Update code
        code = sparse_encode(
            X,
            dictionary,
            algorithm=method,
            alpha=alpha,
            init=code,
            n_jobs=n_jobs,
            positive=positive_code,
            max_iter=method_max_iter,
            verbose=verbose,
        )

        # Update dictionary in place
        _update_dict(
            dictionary,
            X,
            code,
            verbose=verbose,
            random_state=random_state,
            positive=positive_dict,
        )

        # Cost function
        current_cost = 0.5 * np.sum((X - code @ dictionary) ** 2) + alpha * np.sum(
            np.abs(code)
        )
        errors.append(current_cost)

        if ii > 0:
            dE = errors[-2] - errors[-1]
            # assert(dE >= -tol * errors[-1])
            if dE < tol * errors[-1]:
                if verbose == 1:
                    # A line return
                    print("")
                elif verbose:
                    print("--- Convergence reached after %d iterations" % ii)
                break
        if ii % 5 == 0 and callback is not None:
            callback(locals())

    if return_n_iter:
        return code, dictionary, errors, ii + 1
    else:
        return code, dictionary, errors