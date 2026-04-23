def sag(
    X,
    y,
    step_size,
    alpha,
    n_iter=1,
    dloss=None,
    sparse=False,
    sample_weight=None,
    fit_intercept=True,
    saga=False,
):
    n_samples, n_features = X.shape[0], X.shape[1]

    weights = np.zeros(X.shape[1])
    sum_gradient = np.zeros(X.shape[1])
    gradient_memory = np.zeros((n_samples, n_features))

    intercept = 0.0
    intercept_sum_gradient = 0.0
    intercept_gradient_memory = np.zeros(n_samples)

    rng = np.random.RandomState(77)
    decay = 1.0
    seen = set()

    # sparse data has a fixed decay of .01
    if sparse:
        decay = 0.01

    for epoch in range(n_iter):
        for k in range(n_samples):
            idx = int(rng.rand() * n_samples)
            # idx = k
            entry = X[idx]
            seen.add(idx)
            p = np.dot(entry, weights) + intercept
            gradient = dloss(p, y[idx])
            if sample_weight is not None:
                gradient *= sample_weight[idx]
            update = entry * gradient + alpha * weights
            gradient_correction = update - gradient_memory[idx]
            sum_gradient += gradient_correction
            gradient_memory[idx] = update
            if saga:
                weights -= gradient_correction * step_size * (1 - 1.0 / len(seen))

            if fit_intercept:
                gradient_correction = gradient - intercept_gradient_memory[idx]
                intercept_gradient_memory[idx] = gradient
                intercept_sum_gradient += gradient_correction
                gradient_correction *= step_size * (1.0 - 1.0 / len(seen))
                if saga:
                    intercept -= (
                        step_size * intercept_sum_gradient / len(seen) * decay
                    ) + gradient_correction
                else:
                    intercept -= step_size * intercept_sum_gradient / len(seen) * decay

            weights -= step_size * sum_gradient / len(seen)

    return weights, intercept