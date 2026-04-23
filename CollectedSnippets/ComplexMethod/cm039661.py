def fit(self, X, y):
        n_samples, n_features = X.shape
        self.w = np.zeros(n_features, dtype=np.float64)
        self.b = 0.0

        # Mimic SGD's behavior for intercept
        intercept_decay = 1.0
        if issparse(X):
            intercept_decay = SPARSE_INTERCEPT_DECAY
            X = X.toarray()

        for t in range(self.n_iter):
            for i in range(n_samples):
                p = self.project(X[i])
                if self.loss in ("hinge", "squared_hinge"):
                    loss = max(1 - y[i] * p, 0)
                else:
                    loss = max(np.abs(p - y[i]) - self.epsilon, 0)

                sqnorm = np.dot(X[i], X[i])

                if self.loss in ("hinge", "epsilon_insensitive"):
                    step = min(self.C, loss / sqnorm)
                elif self.loss in ("squared_hinge", "squared_epsilon_insensitive"):
                    step = loss / (sqnorm + 1.0 / (2 * self.C))

                if self.loss in ("hinge", "squared_hinge"):
                    step *= y[i]
                else:
                    step *= np.sign(y[i] - p)

                self.w += step * X[i]
                if self.fit_intercept:
                    self.b += intercept_decay * step