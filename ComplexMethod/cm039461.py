def mdi_importance(X_m, X, y):
        n_samples, n_features = X.shape

        features = list(range(n_features))
        features.pop(X_m)
        values = [np.unique(X[:, i]) for i in range(n_features)]

        imp = 0.0

        for k in range(n_features):
            # Weight of each B of size k
            coef = 1.0 / (binomial(k, n_features) * (n_features - k))

            # For all B of size k
            for B in combinations(features, k):
                # For all values B=b
                for b in product(*[values[B[j]] for j in range(k)]):
                    mask_b = np.ones(n_samples, dtype=bool)

                    for j in range(k):
                        mask_b &= X[:, B[j]] == b[j]

                    X_, y_ = X[mask_b, :], y[mask_b]
                    n_samples_b = len(X_)

                    if n_samples_b > 0:
                        children = []

                        for xi in values[X_m]:
                            mask_xi = X_[:, X_m] == xi
                            children.append(y_[mask_xi])

                        imp += (
                            coef
                            * (1.0 * n_samples_b / n_samples)  # P(B=b)
                            * (
                                entropy(y_)
                                - sum(
                                    [
                                        entropy(c) * len(c) / n_samples_b
                                        for c in children
                                    ]
                                )
                            )
                        )

        return imp