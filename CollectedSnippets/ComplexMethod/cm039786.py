def log_marginal_likelihood(
        self, theta=None, eval_gradient=False, clone_kernel=True
    ):
        """Return log-marginal likelihood of theta for training data.

        In the case of multi-class classification, the mean log-marginal
        likelihood of the one-versus-rest classifiers are returned.

        Parameters
        ----------
        theta : array-like of shape (n_kernel_params,), default=None
            Kernel hyperparameters for which the log-marginal likelihood is
            evaluated. In the case of multi-class classification, theta may
            be the  hyperparameters of the compound kernel or of an individual
            kernel. In the latter case, all individual kernel get assigned the
            same theta values. If None, the precomputed log_marginal_likelihood
            of ``self.kernel_.theta`` is returned.

        eval_gradient : bool, default=False
            If True, the gradient of the log-marginal likelihood with respect
            to the kernel hyperparameters at position theta is returned
            additionally. Note that gradient computation is not supported
            for non-binary classification. If True, theta must not be None.

        clone_kernel : bool, default=True
            If True, the kernel attribute is copied. If False, the kernel
            attribute is modified, but may result in a performance improvement.

        Returns
        -------
        log_likelihood : float
            Log-marginal likelihood of theta for training data.

        log_likelihood_gradient : ndarray of shape (n_kernel_params,), optional
            Gradient of the log-marginal likelihood with respect to the kernel
            hyperparameters at position theta.
            Only returned when `eval_gradient` is True.
        """
        check_is_fitted(self)

        if theta is None:
            if eval_gradient:
                raise ValueError("Gradient can only be evaluated for theta!=None")
            return self.log_marginal_likelihood_value_

        theta = np.asarray(theta)
        if self.n_classes_ == 2:
            return self.base_estimator_.log_marginal_likelihood(
                theta, eval_gradient, clone_kernel=clone_kernel
            )
        else:
            if eval_gradient:
                raise NotImplementedError(
                    "Gradient of log-marginal-likelihood not implemented for "
                    "multi-class GPC."
                )
            estimators = self.base_estimator_.estimators_
            n_dims = estimators[0].kernel_.n_dims
            if theta.shape[0] == n_dims:  # use same theta for all sub-kernels
                return np.mean(
                    [
                        estimator.log_marginal_likelihood(
                            theta, clone_kernel=clone_kernel
                        )
                        for i, estimator in enumerate(estimators)
                    ]
                )
            elif theta.shape[0] == n_dims * self.classes_.shape[0]:
                # theta for compound kernel
                return np.mean(
                    [
                        estimator.log_marginal_likelihood(
                            theta[n_dims * i : n_dims * (i + 1)],
                            clone_kernel=clone_kernel,
                        )
                        for i, estimator in enumerate(estimators)
                    ]
                )
            else:
                raise ValueError(
                    "Shape of theta must be either %d or %d. "
                    "Obtained theta with shape %d."
                    % (n_dims, n_dims * self.classes_.shape[0], theta.shape[0])
                )