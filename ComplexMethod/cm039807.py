def generate_data(
    n_samples, n_features, weights, means, precisions, covariance_type, dtype=np.float64
):
    rng = np.random.RandomState(0)

    X = []
    if covariance_type == "spherical":
        for _, (w, m, c) in enumerate(zip(weights, means, precisions["spherical"])):
            X.append(
                rng.multivariate_normal(
                    m, c * np.eye(n_features), int(np.round(w * n_samples))
                ).astype(dtype)
            )
    if covariance_type == "diag":
        for _, (w, m, c) in enumerate(zip(weights, means, precisions["diag"])):
            X.append(
                rng.multivariate_normal(
                    m, np.diag(c), int(np.round(w * n_samples))
                ).astype(dtype)
            )
    if covariance_type == "tied":
        for _, (w, m) in enumerate(zip(weights, means)):
            X.append(
                rng.multivariate_normal(
                    m, precisions["tied"], int(np.round(w * n_samples))
                ).astype(dtype)
            )
    if covariance_type == "full":
        for _, (w, m, c) in enumerate(zip(weights, means, precisions["full"])):
            X.append(
                rng.multivariate_normal(m, c, int(np.round(w * n_samples))).astype(
                    dtype
                )
            )

    X = np.vstack(X)
    return X