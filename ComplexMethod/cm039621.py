def sag_sparse(
    X,
    y,
    step_size,
    alpha,
    n_iter=1,
    dloss=None,
    sample_weight=None,
    sparse=False,
    fit_intercept=True,
    saga=False,
    random_state=0,
):
    if step_size * alpha == 1.0:
        raise ZeroDivisionError(
            "Sparse sag does not handle the case step_size * alpha == 1"
        )
    n_samples, n_features = X.shape[0], X.shape[1]

    weights = np.zeros(n_features)
    sum_gradient = np.zeros(n_features)
    last_updated = np.zeros(n_features, dtype=int)
    gradient_memory = np.zeros(n_samples)
    rng = check_random_state(random_state)
    intercept = 0.0
    intercept_sum_gradient = 0.0
    wscale = 1.0
    decay = 1.0
    seen = set()

    c_sum = np.zeros(n_iter * n_samples)

    # sparse data has a fixed decay of .01
    if sparse:
        decay = 0.01

    counter = 0
    for epoch in range(n_iter):
        for k in range(n_samples):
            # idx = k
            idx = int(rng.rand() * n_samples)
            entry = X[idx]
            seen.add(idx)

            if counter >= 1:
                for j in range(n_features):
                    if last_updated[j] == 0:
                        weights[j] -= c_sum[counter - 1] * sum_gradient[j]
                    else:
                        weights[j] -= (
                            c_sum[counter - 1] - c_sum[last_updated[j] - 1]
                        ) * sum_gradient[j]
                    last_updated[j] = counter

            p = (wscale * np.dot(entry, weights)) + intercept
            gradient = dloss(p, y[idx])

            if sample_weight is not None:
                gradient *= sample_weight[idx]

            update = entry * gradient
            gradient_correction = update - (gradient_memory[idx] * entry)
            sum_gradient += gradient_correction
            if saga:
                for j in range(n_features):
                    weights[j] -= (
                        gradient_correction[j]
                        * step_size
                        * (1 - 1.0 / len(seen))
                        / wscale
                    )

            if fit_intercept:
                gradient_correction = gradient - gradient_memory[idx]
                intercept_sum_gradient += gradient_correction
                gradient_correction *= step_size * (1.0 - 1.0 / len(seen))
                if saga:
                    intercept -= (
                        step_size * intercept_sum_gradient / len(seen) * decay
                    ) + gradient_correction
                else:
                    intercept -= step_size * intercept_sum_gradient / len(seen) * decay

            gradient_memory[idx] = gradient

            wscale *= 1.0 - alpha * step_size
            if counter == 0:
                c_sum[0] = step_size / (wscale * len(seen))
            else:
                c_sum[counter] = c_sum[counter - 1] + step_size / (wscale * len(seen))

            if counter >= 1 and wscale < 1e-9:
                for j in range(n_features):
                    if last_updated[j] == 0:
                        weights[j] -= c_sum[counter] * sum_gradient[j]
                    else:
                        weights[j] -= (
                            c_sum[counter] - c_sum[last_updated[j] - 1]
                        ) * sum_gradient[j]
                    last_updated[j] = counter + 1
                c_sum[counter] = 0
                weights *= wscale
                wscale = 1.0

            counter += 1

    for j in range(n_features):
        if last_updated[j] == 0:
            weights[j] -= c_sum[counter - 1] * sum_gradient[j]
        else:
            weights[j] -= (
                c_sum[counter - 1] - c_sum[last_updated[j] - 1]
            ) * sum_gradient[j]
    weights *= wscale
    return weights, intercept