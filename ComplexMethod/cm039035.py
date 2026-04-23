def _partial_fit(self, X, y, classes=None, _refit=False, sample_weight=None):
        """Actual implementation of Gaussian NB fitting.

        Parameters
        ----------
        X : array-like of shape (n_samples, n_features)
            Training vectors, where `n_samples` is the number of samples and
            `n_features` is the number of features.

        y : array-like of shape (n_samples,)
            Target values.

        classes : array-like of shape (n_classes,), default=None
            List of all the classes that can possibly appear in the y vector.

            Must be provided at the first call to partial_fit, can be omitted
            in subsequent calls.

        _refit : bool, default=False
            If true, act as though this were the first time we called
            _partial_fit (ie, throw away any past fitting and start over).

        sample_weight : array-like of shape (n_samples,), default=None
            Weights applied to individual samples (1. for unweighted).

        Returns
        -------
        self : object
        """
        if _refit:
            self.classes_ = None

        first_call = _check_partial_fit_first_call(self, classes)
        X, y = validate_data(self, X, y, reset=first_call)
        xp, _, device_ = get_namespace_and_device(X)
        float_dtype = _find_matching_floating_dtype(X, xp=xp)
        if sample_weight is not None:
            sample_weight = _check_sample_weight(sample_weight, X, dtype=float_dtype)

        xp_y, _ = get_namespace(y)
        # If the ratio of data variance between dimensions is too small, it
        # will cause numerical errors. To address this, we artificially
        # boost the variance by epsilon, a small fraction of the standard
        # deviation of the largest dimension.
        self.epsilon_ = self.var_smoothing * xp.max(xp.var(X, axis=0))

        if first_call:
            # This is the first call to partial_fit:
            # initialize various cumulative counters
            n_features = X.shape[1]
            n_classes = self.classes_.shape[0]
            self.theta_ = xp.zeros(
                (n_classes, n_features), dtype=float_dtype, device=device_
            )
            self.var_ = xp.zeros(
                (n_classes, n_features), dtype=float_dtype, device=device_
            )

            self.class_count_ = xp.zeros(n_classes, dtype=float_dtype, device=device_)

            # Initialise the class prior
            # Take into account the priors
            if self.priors is not None:
                priors = xp.asarray(self.priors, dtype=float_dtype, device=device_)
                # Check that the provided prior matches the number of classes
                if priors.shape[0] != n_classes:
                    raise ValueError("Number of priors must match number of classes.")
                # Check that the sum is 1
                if not xpx.isclose(xp.sum(priors), 1.0):
                    raise ValueError("The sum of the priors should be 1.")
                # Check that the priors are non-negative
                if xp.any(priors < 0):
                    raise ValueError("Priors must be non-negative.")
                self.class_prior_ = priors
            else:
                # Initialize the priors to zeros for each class
                self.class_prior_ = xp.zeros(
                    self.classes_.shape[0], dtype=float_dtype, device=device_
                )
        else:
            if X.shape[1] != self.theta_.shape[1]:
                msg = "Number of features %d does not match previous data %d."
                raise ValueError(msg % (X.shape[1], self.theta_.shape[1]))
            # Put epsilon back in each time
            self.var_[:, :] -= self.epsilon_

        classes = self.classes_

        unique_y = xp_y.unique_values(y)
        unique_y_in_classes = _isin(unique_y, classes, xp=xp_y)

        if not xp_y.all(unique_y_in_classes):
            raise ValueError(
                "The target label(s) %s in y do not exist in the initial classes %s"
                % (unique_y[~unique_y_in_classes], classes)
            )

        for y_i in unique_y:
            i = int(xp_y.searchsorted(classes, y_i))
            y_i_mask = xp.asarray(y == y_i, device=device_)
            X_i = X[y_i_mask]

            if sample_weight is not None:
                sw_i = sample_weight[y_i_mask]
                N_i = xp.sum(sw_i)
            else:
                sw_i = None
                N_i = X_i.shape[0]

            new_theta, new_sigma = self._update_mean_variance(
                self.class_count_[i], self.theta_[i, :], self.var_[i, :], X_i, sw_i
            )

            self.theta_[i, :] = new_theta
            self.var_[i, :] = new_sigma
            self.class_count_[i] += N_i

        self.var_[:, :] += self.epsilon_

        # Update if only no priors is provided
        if self.priors is None:
            # Empirical prior, with sample_weight taken into account
            self.class_prior_ = self.class_count_ / xp.sum(self.class_count_)

        return self