def _fit_transform(self, X, W=None, H=None, update_H=True):
        """Learn a NMF model for the data X and returns the transformed data.

        Parameters
        ----------
        X : {ndarray, sparse matrix} of shape (n_samples, n_features)
            Data matrix to be decomposed.

        W : array-like of shape (n_samples, n_components), default=None
            If `init='custom'`, it is used as initial guess for the solution.
            If `update_H=False`, it is initialised as an array of zeros, unless
            `solver='mu'`, then it is filled with values calculated by
            `np.sqrt(X.mean() / self._n_components)`.
            If `None`, uses the initialisation method specified in `init`.

        H : array-like of shape (n_components, n_features), default=None
            If `init='custom'`, it is used as initial guess for the solution.
            If `update_H=False`, it is used as a constant, to solve for W only.
            If `None`, uses the initialisation method specified in `init`.

        update_H : bool, default=True
            If True, both W and H will be estimated from initial guesses,
            this corresponds to a call to the `fit_transform` method.
            If False, only W will be estimated, this corresponds to a call
            to the `transform` method.

        Returns
        -------
        W : ndarray of shape (n_samples, n_components)
            Transformed data.

        H : ndarray of shape (n_components, n_features)
            Factorization matrix, sometimes called 'dictionary'.

        n_iter : int
            Actual number of started iterations over the whole dataset.

        n_steps : int
            Number of mini-batches processed.
        """
        check_non_negative(X, "MiniBatchNMF (input X)")
        self._check_params(X)

        if X.min() == 0 and self._beta_loss <= 0:
            raise ValueError(
                "When beta_loss <= 0 and X contains zeros, "
                "the solver may diverge. Please add small values "
                "to X, or use a positive beta_loss."
            )

        n_samples = X.shape[0]

        # initialize or check W and H
        W, H = self._check_w_h(X, W, H, update_H)
        H_buffer = H.copy()

        # Initialize auxiliary matrices
        self._components_numerator = H.copy()
        self._components_denominator = np.ones(H.shape, dtype=H.dtype)

        # Attributes to monitor the convergence
        self._ewa_cost = None
        self._ewa_cost_min = None
        self._no_improvement = 0

        batches = gen_batches(n_samples, self._batch_size)
        batches = itertools.cycle(batches)
        n_steps_per_iter = int(np.ceil(n_samples / self._batch_size))
        n_steps = self.max_iter * n_steps_per_iter

        for i, batch in zip(range(n_steps), batches):
            batch_cost = self._minibatch_step(X[batch], W[batch], H, update_H)

            if update_H and self._minibatch_convergence(
                X[batch], batch_cost, H, H_buffer, n_samples, i, n_steps
            ):
                break

            H_buffer[:] = H

        if self.fresh_restarts:
            W = self._solve_W(X, H, self._transform_max_iter)

        n_steps = i + 1
        n_iter = int(np.ceil(n_steps / n_steps_per_iter))

        if n_iter == self.max_iter and self.tol > 0:
            warnings.warn(
                (
                    f"Maximum number of iterations {self.max_iter} reached. "
                    "Increase it to improve convergence."
                ),
                ConvergenceWarning,
            )

        return W, H, n_iter, n_steps