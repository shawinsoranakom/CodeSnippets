def sample(self, n_samples=1):
        """Generate random samples from the fitted Gaussian distribution.

        Parameters
        ----------
        n_samples : int, default=1
            Number of samples to generate.

        Returns
        -------
        X : array, shape (n_samples, n_features)
            Randomly generated sample.

        y : array, shape (nsamples,)
            Component labels.
        """
        check_is_fitted(self)
        xp, _, device_ = get_namespace_and_device(self.means_)

        if n_samples < 1:
            raise ValueError(
                "Invalid value for 'n_samples': %d . The sampling requires at "
                "least one sample." % (self.n_components)
            )

        _, n_features = self.means_.shape
        rng = check_random_state(self.random_state)
        n_samples_comp = rng.multinomial(
            n_samples, move_to(self.weights_, xp=np, device="cpu")
        )

        if self.covariance_type == "full":
            X = np.vstack(
                [
                    rng.multivariate_normal(mean, covariance, int(sample))
                    for (mean, covariance, sample) in zip(
                        move_to(self.means_, xp=np, device="cpu"),
                        move_to(self.covariances_, xp=np, device="cpu"),
                        n_samples_comp,
                    )
                ]
            )
        elif self.covariance_type == "tied":
            X = np.vstack(
                [
                    rng.multivariate_normal(
                        mean,
                        move_to(self.covariances_, xp=np, device="cpu"),
                        int(sample),
                    )
                    for (mean, sample) in zip(
                        move_to(self.means_, xp=np, device="cpu"), n_samples_comp
                    )
                ]
            )
        else:
            X = np.vstack(
                [
                    mean
                    + rng.standard_normal(size=(sample, n_features))
                    * np.sqrt(covariance)
                    for (mean, covariance, sample) in zip(
                        move_to(self.means_, xp=np, device="cpu"),
                        move_to(self.covariances_, xp=np, device="cpu"),
                        n_samples_comp,
                    )
                ]
            )

        y = xp.concat(
            [
                xp.full(int(n_samples_comp[i]), i, dtype=xp.int64, device=device_)
                for i in range(len(n_samples_comp))
            ]
        )

        max_float_dtype = _max_precision_float_dtype(xp=xp, device=device_)
        return xp.asarray(X, dtype=max_float_dtype, device=device_), y