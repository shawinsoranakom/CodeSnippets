def fit(self, X, y):
        """Fit the model according to the given training data and parameters.

        .. versionchanged:: 0.19
            ``store_covariances`` has been moved to main constructor as
            ``store_covariance``.

        .. versionchanged:: 0.19
            ``tol`` has been moved to main constructor.

        Parameters
        ----------
        X : array-like of shape (n_samples, n_features)
            Training vector, where `n_samples` is the number of samples and
            `n_features` is the number of features.

        y : array-like of shape (n_samples,)
            Target values (integers).

        Returns
        -------
        self : object
            Fitted estimator.
        """
        X, y = validate_data(self, X, y)
        check_classification_targets(y)
        self.classes_ = np.unique(y)
        n_samples, n_features = X.shape
        n_classes = len(self.classes_)
        if n_classes < 2:
            raise ValueError(
                "The number of classes has to be greater than one. Got "
                f"{n_classes} class."
            )
        if self.priors is None:
            _, cnts = np.unique(y, return_counts=True)
            self.priors_ = cnts / float(n_samples)
        else:
            self.priors_ = np.array(self.priors)

        if self.solver == "svd":
            if self.shrinkage is not None:
                # Support for `shrinkage` could be implemented as in
                # https://github.com/scikit-learn/scikit-learn/issues/32590
                raise NotImplementedError("shrinkage not supported with 'svd' solver.")
            if self.covariance_estimator is not None:
                raise ValueError(
                    "covariance_estimator is not supported with solver='svd'. "
                    "Try solver='eigen' instead."
                )
            specific_solver = self._solve_svd
        elif self.solver == "eigen":
            specific_solver = self._solve_eigen

        means = []
        cov = []
        scalings = []
        rotations = []
        for class_idx, class_label in enumerate(self.classes_):
            X_class = X[y == class_label, :]
            if len(X_class) == 1:
                raise ValueError(
                    "y has only 1 sample in class %s, covariance is ill defined."
                    % str(self.classes_[class_idx])
                )

            mean_class = X_class.mean(0)
            means.append(mean_class)

            scaling_class, rotation_class, cov_class = specific_solver(X_class)

            rank = np.sum(scaling_class > self.tol)
            if rank < n_features:
                n_samples_class = X_class.shape[0]
                if self.solver == "svd" and n_samples_class <= n_features:
                    raise linalg.LinAlgError(
                        f"The covariance matrix of class {class_label} is not full "
                        f"rank. When using `solver='svd'` the number of samples in "
                        f"each class should be more than the number of features, but "
                        f"class {class_label} has {n_samples_class} samples and "
                        f"{n_features} features. Try using `solver='eigen'` and "
                        f"setting the parameter `shrinkage` for regularization."
                    )
                else:
                    msg_param = "shrinkage" if self.solver == "eigen" else "reg_param"
                    raise linalg.LinAlgError(
                        f"The covariance matrix of class {class_label} is not full "
                        f"rank. Increase the value of `{msg_param}` to reduce the "
                        f"collinearity.",
                    )

            cov.append(cov_class)
            scalings.append(scaling_class)
            rotations.append(rotation_class)

        if self.store_covariance:
            self.covariance_ = cov
        self.means_ = np.asarray(means)
        self.scalings_ = scalings
        self.rotations_ = rotations
        return self