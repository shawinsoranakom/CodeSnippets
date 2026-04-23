def fit(self, X, y=None, **params):
        """Fit the GraphicalLasso covariance model to X.

        Parameters
        ----------
        X : array-like of shape (n_samples, n_features)
            Data from which to compute the covariance estimate.

        y : Ignored
            Not used, present for API consistency by convention.

        **params : dict, default=None
            Parameters to be passed to the CV splitter and the
            cross_val_score function.

            .. versionadded:: 1.5
                Only available if `enable_metadata_routing=True`,
                which can be set by using
                ``sklearn.set_config(enable_metadata_routing=True)``.
                See :ref:`Metadata Routing User Guide <metadata_routing>` for
                more details.

        Returns
        -------
        self : object
            Returns the instance itself.
        """
        # Covariance does not make sense for a single feature
        _raise_for_params(params, self, "fit")

        X = validate_data(self, X, ensure_min_features=2)
        if self.assume_centered:
            self.location_ = np.zeros(X.shape[1])
        else:
            self.location_ = X.mean(0)
        emp_cov = empirical_covariance(X, assume_centered=self.assume_centered)

        cv = check_cv(self.cv, y, classifier=False)

        # List of (alpha, scores, covs)
        path = list()
        n_alphas = self.alphas
        inner_verbose = max(0, self.verbose - 1)

        if _is_arraylike_not_scalar(n_alphas):
            for alpha in self.alphas:
                check_scalar(
                    alpha,
                    "alpha",
                    Real,
                    min_val=0,
                    max_val=np.inf,
                    include_boundaries="right",
                )
            alphas = self.alphas
            n_refinements = 1
        else:
            n_refinements = self.n_refinements
            alpha_1 = alpha_max(emp_cov)
            alpha_0 = 1e-2 * alpha_1
            alphas = np.logspace(np.log10(alpha_0), np.log10(alpha_1), n_alphas)[::-1]

        if _routing_enabled():
            routed_params = process_routing(self, "fit", **params)
        else:
            routed_params = Bunch(splitter=Bunch(split={}))

        t0 = time.time()
        for i in range(n_refinements):
            with warnings.catch_warnings():
                # No need to see the convergence warnings on this grid:
                # they will always be points that will not converge
                # during the cross-validation
                warnings.simplefilter("ignore", ConvergenceWarning)
                # Compute the cross-validated loss on the current grid

                # NOTE: Warm-restarting graphical_lasso_path has been tried,
                # and this did not allow to gain anything
                # (same execution time with or without).
                this_path = Parallel(n_jobs=self.n_jobs, verbose=self.verbose)(
                    delayed(graphical_lasso_path)(
                        X[train],
                        alphas=alphas,
                        X_test=X[test],
                        mode=self.mode,
                        tol=self.tol,
                        enet_tol=self.enet_tol,
                        max_iter=int(0.1 * self.max_iter),
                        verbose=inner_verbose,
                        eps=self.eps,
                    )
                    for train, test in cv.split(X, y, **routed_params.splitter.split)
                )

            # Little danse to transform the list in what we need
            covs, _, scores = zip(*this_path)
            covs = zip(*covs)
            scores = zip(*scores)
            path.extend(zip(alphas, scores, covs))
            path = sorted(path, key=operator.itemgetter(0), reverse=True)

            # Find the maximum (avoid using built in 'max' function to
            # have a fully-reproducible selection of the smallest alpha
            # in case of equality)
            best_score = -np.inf
            last_finite_idx = 0
            for index, (alpha, scores, _) in enumerate(path):
                this_score = np.mean(scores)
                if this_score >= 0.1 / np.finfo(np.float64).eps:
                    this_score = np.nan
                if np.isfinite(this_score):
                    last_finite_idx = index
                if this_score >= best_score:
                    best_score = this_score
                    best_index = index

            # Refine the grid
            if best_index == 0:
                # We do not need to go back: we have chosen
                # the highest value of alpha for which there are
                # non-zero coefficients
                alpha_1 = path[0][0]
                alpha_0 = path[1][0]
            elif best_index == last_finite_idx and not best_index == len(path) - 1:
                # We have non-converged models on the upper bound of the
                # grid, we need to refine the grid there
                alpha_1 = path[best_index][0]
                alpha_0 = path[best_index + 1][0]
            elif best_index == len(path) - 1:
                alpha_1 = path[best_index][0]
                alpha_0 = 0.01 * path[best_index][0]
            else:
                alpha_1 = path[best_index - 1][0]
                alpha_0 = path[best_index + 1][0]

            if not _is_arraylike_not_scalar(n_alphas):
                alphas = np.logspace(np.log10(alpha_1), np.log10(alpha_0), n_alphas + 2)
                alphas = alphas[1:-1]

            if self.verbose and n_refinements > 1:
                print(
                    "[GraphicalLassoCV] Done refinement % 2i out of %i: % 3is"
                    % (i + 1, n_refinements, time.time() - t0)
                )

        path = list(zip(*path))
        grid_scores = list(path[1])
        alphas = list(path[0])
        # Finally, compute the score with alpha = 0
        alphas.append(0)
        grid_scores.append(
            cross_val_score(
                EmpiricalCovariance(),
                X,
                cv=cv,
                n_jobs=self.n_jobs,
                verbose=inner_verbose,
                params=params,
            )
        )
        grid_scores = np.array(grid_scores)

        self.cv_results_ = {"alphas": np.array(alphas)}

        for i in range(grid_scores.shape[1]):
            self.cv_results_[f"split{i}_test_score"] = grid_scores[:, i]

        self.cv_results_["mean_test_score"] = np.mean(grid_scores, axis=1)
        self.cv_results_["std_test_score"] = np.std(grid_scores, axis=1)

        best_alpha = alphas[best_index]
        self.alpha_ = best_alpha

        # Finally fit the model with the selected alpha
        self.covariance_, self.precision_, self.costs_, self.n_iter_ = _graphical_lasso(
            emp_cov,
            alpha=best_alpha,
            mode=self.mode,
            tol=self.tol,
            enet_tol=self.enet_tol,
            max_iter=self.max_iter,
            verbose=inner_verbose,
            eps=self.eps,
        )
        return self