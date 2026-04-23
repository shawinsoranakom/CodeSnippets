def fit(self, X, y, sample_weight=None, **params):
        """Fit model with internal cross-validation and with coordinate descent.

        Fit is on grid of alphas and best alpha estimated by cross-validation.

        Parameters
        ----------
        X : {array-like, sparse matrix} of shape (n_samples, n_features)
            Training data. Pass directly as Fortran-contiguous data
            to avoid unnecessary memory duplication. If y is mono-output,
            X can be sparse. Note that large sparse matrices and arrays
            requiring `int64` indices are not accepted.

        y : array-like of shape (n_samples,) or (n_samples, n_targets)
            Target values.

        sample_weight : float or array-like of shape (n_samples,), \
                default=None
            Sample weights used for fitting and evaluation of the weighted
            mean squared error of each cv-fold. Note that the cross validated
            MSE that is finally used to find the best model is the unweighted
            mean over the (weighted) MSEs of each test fold.

        **params : dict, default=None
            Parameters to be passed to the CV splitter.

            .. versionadded:: 1.4
                Only available if `enable_metadata_routing=True`,
                which can be set by using
                ``sklearn.set_config(enable_metadata_routing=True)``.
                See :ref:`Metadata Routing User Guide <metadata_routing>` for
                more details.

        Returns
        -------
        self : object
            Returns an instance of fitted model.
        """
        _raise_for_params(params, self, "fit")

        # This makes sure that there is no duplication in memory.
        # Dealing right with copy_X is important in the following:
        # Multiple functions touch X and subsamples of X and can induce a
        # lot of duplication of memory.
        # There is no need copy X if the model is fit without an intercept.
        copy_X = self.copy_X and self.fit_intercept  # TODO: Sample_weights?

        check_y_params = dict(
            copy=False, dtype=[np.float64, np.float32], ensure_2d=False
        )
        if isinstance(X, np.ndarray) or sparse.issparse(X):
            # Keep a reference to X
            reference_to_old_X = X
            # Let us not impose Fortran-contiguity so far: In the cross-validation
            # loop, rows of X will be subsampled and produce non-F-contiguous X_fold
            # anyway. _path_residual will take care about it.

            # Need to validate separately here.
            # We can't pass multi_output=True because that would allow y to be
            # csr. We also want to allow y to be 64 or 32 but check_X_y only
            # allows to convert for 64.
            check_X_params = dict(
                accept_sparse="csc",
                dtype=[np.float64, np.float32],
                force_writeable=True,
                copy=False,
                accept_large_sparse=False,
            )
            X, y = validate_data(
                self, X, y, validate_separately=(check_X_params, check_y_params)
            )
            if sparse.issparse(X):
                if hasattr(reference_to_old_X, "data") and not np.may_share_memory(
                    reference_to_old_X.data, X.data
                ):
                    # X is a sparse matrix and has been copied. No need to copy again.
                    copy_X = False
            elif not np.may_share_memory(reference_to_old_X, X):
                # X has been copied. No need to copy again.
                copy_X = False
            del reference_to_old_X
        else:
            # Need to validate separately here.
            # We can't pass multi_output=True because that would allow y to be
            # csr. We also want to allow y to be 64 or 32 but check_X_y only
            # allows to convert for 64.
            check_X_params = dict(
                accept_sparse="csc",
                dtype=[np.float64, np.float32],
                order="F",
                force_writeable=True,
                copy=copy_X,
            )
            X, y = validate_data(
                self, X, y, validate_separately=(check_X_params, check_y_params)
            )
            copy_X = False

        check_consistent_length(X, y)

        if not self._is_multitask():
            if y.ndim > 1 and y.shape[1] > 1:
                raise ValueError(
                    "For multi-task outputs, use MultiTask%s" % self.__class__.__name__
                )
            y = column_or_1d(y, warn=True)
        else:
            if y.ndim == 1:
                raise ValueError(
                    "For mono-task outputs, use %sCV" % self.__class__.__name__[9:]
                )

        if isinstance(sample_weight, numbers.Number):
            sample_weight = None
        if sample_weight is not None:
            sample_weight = _check_sample_weight(sample_weight, X, dtype=X.dtype)

        model = self._get_estimator()

        # All LinearModelCV parameters except 'cv' are acceptable
        path_params = self.get_params()

        # fit_intercept is not a parameter of the path function
        path_params.pop("fit_intercept", None)

        if "l1_ratio" in path_params:
            l1_ratios = np.atleast_1d(path_params["l1_ratio"])
            # For the first path, we need to set l1_ratio
            path_params["l1_ratio"] = l1_ratios[0]
        else:
            l1_ratios = [
                1,
            ]
        path_params.pop("cv", None)
        path_params.pop("n_jobs", None)

        n_l1_ratio = len(l1_ratios)

        check_scalar_alpha = partial(
            check_scalar,
            target_type=Real,
            min_val=0.0,
            include_boundaries="left",
        )

        if isinstance(self.alphas, Integral):
            alphas = [
                _alpha_grid(
                    X,
                    y,
                    l1_ratio=l1_ratio,
                    fit_intercept=self.fit_intercept,
                    # Note: MultiTaskElasticNetCV has no attribute 'positive'
                    positive=getattr(self, "positive", False),
                    eps=self.eps,
                    n_alphas=self.alphas,
                    sample_weight=sample_weight,
                )
                for l1_ratio in l1_ratios
            ]
        else:
            # Making sure alphas entries are scalars.
            for index, alpha in enumerate(self.alphas):
                check_scalar_alpha(alpha, f"alphas[{index}]")
            # Making sure alphas is properly ordered.
            alphas = np.tile(np.sort(self.alphas)[::-1], (n_l1_ratio, 1))

        # We want n_alphas to be the number of alphas used for each l1_ratio.
        n_alphas = len(alphas[0])
        path_params.update({"n_alphas": n_alphas})

        path_params["copy_X"] = copy_X
        # We are not computing in parallel, we can modify X
        # inplace in the folds
        if effective_n_jobs(self.n_jobs) > 1:
            path_params["copy_X"] = False

        # init cross-validation generator
        cv = check_cv(self.cv)

        if _routing_enabled():
            routed_params = process_routing(
                self,
                "fit",
                sample_weight=sample_weight,
                **params,
            )
        else:
            routed_params = Bunch()
            routed_params.splitter = Bunch(split=Bunch())

        # Compute path for all folds and compute MSE to get the best alpha
        folds = list(cv.split(X, y, **routed_params.splitter.split))
        best_mse = np.inf

        # We do a double for loop folded in one, in order to be able to
        # iterate in parallel on l1_ratio and folds
        jobs = (
            delayed(_path_residuals)(
                X,
                y,
                sample_weight,
                train,
                test,
                self.fit_intercept,
                self.path,
                path_params,
                alphas=this_alphas,
                l1_ratio=this_l1_ratio,
                X_order="F",
                dtype=X.dtype.type,
            )
            for this_l1_ratio, this_alphas in zip(l1_ratios, alphas)
            for train, test in folds
        )
        mse_paths = Parallel(
            n_jobs=self.n_jobs,
            verbose=self.verbose,
            prefer="threads",
        )(jobs)
        mse_paths = np.reshape(mse_paths, (n_l1_ratio, len(folds), -1))
        # The mean is computed over folds.
        mean_mse = np.mean(mse_paths, axis=1)
        self.mse_path_ = np.squeeze(np.moveaxis(mse_paths, 2, 1))
        for l1_ratio, l1_alphas, mse_alphas in zip(l1_ratios, alphas, mean_mse):
            i_best_alpha = np.argmin(mse_alphas)
            this_best_mse = mse_alphas[i_best_alpha]
            if this_best_mse < best_mse:
                best_alpha = l1_alphas[i_best_alpha]
                best_l1_ratio = l1_ratio
                best_mse = this_best_mse

        self.l1_ratio_ = best_l1_ratio
        self.alpha_ = best_alpha
        if isinstance(self.alphas, Integral):
            self.alphas_ = np.asarray(alphas)
            if n_l1_ratio == 1:
                self.alphas_ = self.alphas_[0]
        # Remove duplicate alphas in case alphas is provided.
        else:
            self.alphas_ = np.asarray(alphas[0])

        # Refit the model with the parameters selected
        common_params = {
            name: value
            for name, value in self.get_params().items()
            if name in model.get_params()
        }
        model.set_params(**common_params)
        model.alpha = best_alpha
        model.l1_ratio = best_l1_ratio
        model.copy_X = copy_X
        precompute = getattr(self, "precompute", None)
        if isinstance(precompute, str) and precompute == "auto":
            model.precompute = False

        if sample_weight is None:
            # MultiTaskElasticNetCV does not (yet) support sample_weight, even
            # not sample_weight=None.
            model.fit(X, y)
        else:
            model.fit(X, y, sample_weight=sample_weight)
        if not hasattr(self, "l1_ratio"):
            del self.l1_ratio_
        self.coef_ = model.coef_
        self.intercept_ = model.intercept_
        self.dual_gap_ = model.dual_gap_
        self.n_iter_ = model.n_iter_
        return self