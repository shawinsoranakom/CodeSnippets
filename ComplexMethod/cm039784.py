def fit(self, X, y):
        """Fit Gaussian process classification model.

        Parameters
        ----------
        X : array-like of shape (n_samples, n_features) or list of object
            Feature vectors or other representations of training data.

        y : array-like of shape (n_samples,)
            Target values, must be binary.

        Returns
        -------
        self : returns an instance of self.
        """
        if self.kernel is None:  # Use an RBF kernel as default
            self.kernel_ = C(1.0, constant_value_bounds="fixed") * RBF(
                1.0, length_scale_bounds="fixed"
            )
        else:
            self.kernel_ = clone(self.kernel)

        self.rng = check_random_state(self.random_state)

        self.X_train_ = np.copy(X) if self.copy_X_train else X

        # Encode class labels and check that it is a binary classification
        # problem
        label_encoder = LabelEncoder()
        self.y_train_ = label_encoder.fit_transform(y)
        self.classes_ = label_encoder.classes_
        if self.classes_.size > 2:
            raise ValueError(
                "%s supports only binary classification. y contains classes %s"
                % (self.__class__.__name__, self.classes_)
            )
        elif self.classes_.size == 1:
            raise ValueError(
                "{0:s} requires 2 classes; got {1:d} class".format(
                    self.__class__.__name__, self.classes_.size
                )
            )

        if self.optimizer is not None and self.kernel_.n_dims > 0:
            # Choose hyperparameters based on maximizing the log-marginal
            # likelihood (potentially starting from several initial values)
            def obj_func(theta, eval_gradient=True):
                if eval_gradient:
                    lml, grad = self.log_marginal_likelihood(
                        theta, eval_gradient=True, clone_kernel=False
                    )
                    return -lml, -grad
                else:
                    return -self.log_marginal_likelihood(theta, clone_kernel=False)

            # First optimize starting from theta specified in kernel
            optima = [
                self._constrained_optimization(
                    obj_func, self.kernel_.theta, self.kernel_.bounds
                )
            ]

            # Additional runs are performed from log-uniform chosen initial
            # theta
            if self.n_restarts_optimizer > 0:
                if not np.isfinite(self.kernel_.bounds).all():
                    raise ValueError(
                        "Multiple optimizer restarts (n_restarts_optimizer>0) "
                        "requires that all bounds are finite."
                    )
                bounds = self.kernel_.bounds
                for iteration in range(self.n_restarts_optimizer):
                    theta_initial = np.exp(self.rng.uniform(bounds[:, 0], bounds[:, 1]))
                    optima.append(
                        self._constrained_optimization(obj_func, theta_initial, bounds)
                    )
            # Select result from run with minimal (negative) log-marginal
            # likelihood
            lml_values = list(map(itemgetter(1), optima))
            self.kernel_.theta = optima[np.argmin(lml_values)][0]
            self.kernel_._check_bounds_params()

            self.log_marginal_likelihood_value_ = -np.min(lml_values)
        else:
            self.log_marginal_likelihood_value_ = self.log_marginal_likelihood(
                self.kernel_.theta
            )

        # Precompute quantities required for predictions which are independent
        # of actual query points
        K = self.kernel_(self.X_train_)

        _, (self.pi_, self.W_sr_, self.L_, _, _) = self._posterior_mode(
            K, return_temporaries=True
        )

        return self