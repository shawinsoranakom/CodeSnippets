def fit(self, X, y, sample_weight=None, **params):
        """Fit the model according to the given training data.

        Parameters
        ----------
        X : {array-like, sparse matrix} of shape (n_samples, n_features)
            Training vector, where `n_samples` is the number of samples and
            `n_features` is the number of features.

        y : array-like of shape (n_samples,)
            Target vector relative to X.

        sample_weight : array-like of shape (n_samples,) default=None
            Array of weights that are assigned to individual samples.
            If not provided, then each sample is given unit weight.

        **params : dict
            Parameters to pass to the underlying splitter and scorer.

            .. versionadded:: 1.4

        Returns
        -------
        self : object
            Fitted LogisticRegressionCV estimator.
        """
        _raise_for_params(params, self, "fit")

        if isinstance(self.l1_ratios, str) and self.l1_ratios == "warn":
            l1_ratios = None
            warnings.warn(
                (
                    "The default value for l1_ratios will change from None to (0.0,) "
                    "in version 1.10. From version 1.10 onwards, only array-like "
                    "with values in [0, 1] will be allowed, None will be forbidden. "
                    "To avoid this warning, explicitly set a value, "
                    "e.g. l1_ratios=(0,)."
                ),
                FutureWarning,
            )
        else:
            l1_ratios = self.l1_ratios

        if self.penalty == "deprecated":
            if self.l1_ratios is None:
                warnings.warn(
                    (
                        "'l1_ratios=None' was deprecated in version 1.8 and will "
                        "trigger an error in 1.10. Use an array-like with values"
                        "in [0, 1] instead."
                    ),
                    FutureWarning,
                )
            if np.all(np.asarray(l1_ratios) == 0) or l1_ratios is None:
                penalty = "l2"
            elif np.all(np.asarray(l1_ratios) == 1):
                penalty = "l1"
            else:
                penalty = "elasticnet"
        else:
            penalty = self.penalty
            warnings.warn(
                (
                    "'penalty' was deprecated in version 1.8 and will be removed in"
                    " 1.10. To avoid this warning, leave 'penalty' set to its default"
                    " value and use 'l1_ratios' instead."
                    " Use l1_ratios=(0,) instead of penalty='l2' "
                    " and l1_ratios=(1,) instead of penalty='l1'."
                ),
                FutureWarning,
            )

        if self.scoring == "warn":
            warnings.warn(
                "The default value of the parameter 'scoring' will change from None, "
                "i.e. accuracy, to 'neg_log_loss' in version 1.11. To silence this "
                "warning, explicitly set the scoring parameter: "
                "scoring='neg_log_loss' for the new, scoring='accuracy' or "
                "scoring=None for the old default.",
                FutureWarning,
            )
            scoring = None
        else:
            scoring = self.scoring

        if self.use_legacy_attributes == "warn":
            warnings.warn(
                f"The fitted attributes of {self.__class__.__name__} will be "
                "simplified in scikit-learn 1.10 to remove redundancy. Set"
                "`use_legacy_attributes=False` to enable the new behavior now, or "
                "set it to `True` to silence this warning during the transition period "
                "while keeping the deprecated behavior for the time being. The default "
                "value of use_legacy_attributes will change from True to False in "
                f"scikit-learn 1.10. See the docstring of {self.__class__.__name__} "
                "for more details.",
                FutureWarning,
            )
            use_legacy_attributes = True
        else:
            use_legacy_attributes = self.use_legacy_attributes

        solver = _check_solver(self.solver, penalty, self.dual)

        if penalty == "elasticnet":
            if (
                l1_ratios is None
                or len(l1_ratios) == 0
                or any(
                    (
                        not isinstance(l1_ratio, numbers.Number)
                        or l1_ratio < 0
                        or l1_ratio > 1
                    )
                    for l1_ratio in l1_ratios
                )
            ):
                raise ValueError(
                    "l1_ratios must be an array-like of numbers between "
                    "0 and 1; got (l1_ratios=%r)" % l1_ratios
                )
            l1_ratios_ = l1_ratios
        else:
            if l1_ratios is not None and self.penalty != "deprecated":
                warnings.warn(
                    "l1_ratios parameter is only used when penalty "
                    "is 'elasticnet'. Got (penalty={})".format(penalty)
                )

            if l1_ratios is None:
                l1_ratios_ = [None]
            else:
                l1_ratios_ = l1_ratios

        X, y = validate_data(
            self,
            X,
            y,
            accept_sparse="csr",
            dtype=np.float64,
            order="C",
            accept_large_sparse=solver not in ["liblinear", "sag", "saga"],
        )
        n_features = X.shape[1]
        check_classification_targets(y)

        class_weight = self.class_weight

        # Encode for string labels
        label_encoder = LabelEncoder().fit(y)

        # The original class labels
        classes_only_pos_if_binary = self.classes_ = label_encoder.classes_
        n_classes = len(self.classes_)
        is_binary = n_classes == 2

        if n_classes < 2:
            raise ValueError(
                "This solver needs samples of at least 2 classes"
                " in the data, but the data contains only one"
                f" class: {self.classes_[0]}."
            )

        if solver in ["sag", "saga"]:
            max_squared_sum = row_norms(X, squared=True).max()
        else:
            max_squared_sum = None

        if _routing_enabled():
            routed_params = process_routing(
                self,
                "fit",
                sample_weight=sample_weight,
                **params,
            )
        else:
            routed_params = Bunch()
            routed_params.splitter = Bunch(split={})
            routed_params.scorer = Bunch(score=params)
            if sample_weight is not None:
                routed_params.scorer.score["sample_weight"] = sample_weight

        # init cross-validation generator
        cv = check_cv(self.cv, y, classifier=True)
        folds = list(cv.split(X, y, **routed_params.splitter.split))

        if isinstance(class_weight, dict):
            if not (set(class_weight.keys()) <= set(self.classes_)):
                msg = (
                    "The given class_weight dict must have the class labels as keys; "
                    f"classes={self.classes_} but key={class_weight.keys()}"
                )
                raise ValueError(msg)
        elif class_weight == "balanced":
            # compute the class weights for the entire dataset y
            class_weight = compute_class_weight(
                class_weight,
                classes=self.classes_,
                y=y,
                sample_weight=sample_weight,
            )
            class_weight = dict(zip(self.classes_, class_weight))

        if is_binary:
            n_classes = 1
            classes_only_pos_if_binary = classes_only_pos_if_binary[1:]

        path_func = delayed(_log_reg_scoring_path)

        # The SAG solver releases the GIL so it's more efficient to use
        # threads for this solver.
        if self.solver in ["sag", "saga"]:
            prefer = "threads"
        else:
            prefer = "processes"

        fold_coefs_ = Parallel(n_jobs=self.n_jobs, verbose=self.verbose, prefer=prefer)(
            path_func(
                X,
                y,
                train,
                test,
                classes=self.classes_,
                Cs=self.Cs,
                fit_intercept=self.fit_intercept,
                penalty=penalty,
                dual=self.dual,
                solver=solver,
                tol=self.tol,
                max_iter=self.max_iter,
                verbose=self.verbose,
                class_weight=class_weight,
                scoring=scoring,
                intercept_scaling=self.intercept_scaling,
                random_state=self.random_state,
                max_squared_sum=max_squared_sum,
                sample_weight=sample_weight,
                l1_ratio=l1_ratio,
                score_params=routed_params.scorer.score,
            )
            for train, test in folds
            for l1_ratio in l1_ratios_
        )

        # fold_coefs_ is a list and would have shape (n_folds * n_l1_ratios, ..)
        # After reshaping,
        # - coefs_paths is of shape (n_classes, n_folds, n_Cs, n_l1_ratios, n_features)
        # - scores is of shape (n_classes, n_folds, n_Cs, n_l1_ratios)
        # - n_iter is of shape (1, n_folds, n_Cs, n_l1_ratios)
        coefs_paths, Cs, scores, n_iter_ = zip(*fold_coefs_)
        self.Cs_ = Cs[0]  # the same for all folds and l1_ratios
        if is_binary:
            coefs_paths = np.reshape(
                coefs_paths, (len(folds), len(l1_ratios_), len(self.Cs_), -1)
            )
            # coefs_paths.shape = (n_folds, n_l1_ratios, n_Cs, n_features)
            coefs_paths = np.swapaxes(coefs_paths, 1, 2)[None, ...]
        else:
            coefs_paths = np.reshape(
                coefs_paths, (len(folds), len(l1_ratios_), len(self.Cs_), n_classes, -1)
            )
            # coefs_paths.shape = (n_folds, n_l1_ratios, n_Cs, n_classes, n_features)
            coefs_paths = np.moveaxis(coefs_paths, (0, 1, 3), (1, 3, 0))
        # n_iter_.shape = (n_folds, n_l1_ratios, n_Cs)
        n_iter_ = np.reshape(n_iter_, (len(folds), len(l1_ratios_), len(self.Cs_)))
        self.n_iter_ = np.swapaxes(n_iter_, 1, 2)[None, ...]
        # scores.shape = (n_folds, n_l1_ratios, n_Cs)
        scores = np.reshape(scores, (len(folds), len(l1_ratios_), len(self.Cs_)))
        scores = np.swapaxes(scores, 1, 2)[None, ...]
        # repeat same scores across all classes
        scores = np.tile(scores, (n_classes, 1, 1, 1))
        self.scores_ = dict(zip(classes_only_pos_if_binary, scores))
        self.coefs_paths_ = dict(zip(classes_only_pos_if_binary, coefs_paths))

        self.C_ = list()
        self.l1_ratio_ = list()
        self.coef_ = np.empty((n_classes, n_features))
        self.intercept_ = np.zeros(n_classes)

        # All scores are the same across classes
        scores = self.scores_[classes_only_pos_if_binary[0]]

        if self.refit:
            # best_index over folds
            scores_sum = scores.sum(axis=0)  # shape (n_cs, n_l1_ratios)
            best_index = np.unravel_index(np.argmax(scores_sum), scores_sum.shape)

            C_ = self.Cs_[best_index[0]]
            self.C_.append(C_)

            l1_ratio_ = l1_ratios_[best_index[1]]
            self.l1_ratio_.append(l1_ratio_)

            if is_binary:
                coef_init = np.mean(coefs_paths[0, :, *best_index, :], axis=0)
            else:
                coef_init = np.mean(coefs_paths[:, :, *best_index, :], axis=1)

            # Note that y is label encoded
            w, _, _ = _logistic_regression_path(
                X,
                y,
                classes=self.classes_,
                Cs=[C_],
                solver=solver,
                fit_intercept=self.fit_intercept,
                coef=coef_init,
                max_iter=self.max_iter,
                tol=self.tol,
                penalty=penalty,
                class_weight=class_weight,
                verbose=max(0, self.verbose - 1),
                random_state=self.random_state,
                check_input=False,
                max_squared_sum=max_squared_sum,
                sample_weight=sample_weight,
                l1_ratio=l1_ratio_,
            )
            w = w[0]

        else:
            # Take the best scores across every fold and the average of
            # all coefficients corresponding to the best scores.
            n_folds, n_cs, n_l1_ratios = scores.shape
            scores = scores.reshape(n_folds, -1)  # (n_folds, n_cs * n_l1_ratios)
            best_indices = np.argmax(scores, axis=1)  # (n_folds,)
            best_indices = np.unravel_index(best_indices, (n_cs, n_l1_ratios))
            best_indices = list(zip(*best_indices))  # (n_folds, 2)
            # each row of best_indices has the 2 indices for Cs and l1_ratios
            if is_binary:
                w = np.mean(
                    [coefs_paths[0, i, *best_indices[i], :] for i in range(len(folds))],
                    axis=0,
                )
            else:
                w = np.mean(
                    [
                        coefs_paths[:, i, best_indices[i][0], best_indices[i][1], :]
                        for i in range(len(folds))
                    ],
                    axis=0,
                )

            best_indices = np.asarray(best_indices)
            best_indices_C = best_indices[:, 0]
            self.C_.append(np.mean(self.Cs_[best_indices_C]))

            if penalty == "elasticnet":
                best_indices_l1 = best_indices[:, 1]
                self.l1_ratio_.append(np.mean(l1_ratios_[best_indices_l1]))
            else:
                self.l1_ratio_.append(None)

        if is_binary:
            self.coef_ = w[:, :n_features] if w.ndim == 2 else w[:n_features][None, :]
            if self.fit_intercept:
                self.intercept_[0] = w[0, -1] if w.ndim == 2 else w[-1]
        else:
            self.C_ = np.tile(self.C_, n_classes)
            self.l1_ratio_ = np.tile(self.l1_ratio_, n_classes)
            self.coef_ = w[:, :n_features]
            if self.fit_intercept:
                self.intercept_ = w[:, -1]

        self.C_ = np.asarray(self.C_)
        self.l1_ratio_ = np.asarray(self.l1_ratio_)
        self.l1_ratios_ = np.asarray(l1_ratios_)
        if l1_ratios is None:
            # if elasticnet was not used, remove the l1_ratios dimension of some
            # attributes
            for cls, coefs_path in self.coefs_paths_.items():
                self.coefs_paths_[cls] = coefs_path[:, :, 0, :]
            for cls, score in self.scores_.items():
                self.scores_[cls] = score[:, :, 0]
            self.n_iter_ = self.n_iter_[:, :, :, 0]

        if not use_legacy_attributes:
            n_folds = len(folds)
            n_cs = self.Cs_.size
            n_dof = X.shape[1] + int(self.fit_intercept)
            self.C_ = float(self.C_[0])
            newpaths = np.concatenate(list(self.coefs_paths_.values()))
            newscores = self.scores_[
                classes_only_pos_if_binary[0]
            ]  # same for all classes
            newniter = self.n_iter_[0]
            if l1_ratios is None:
                if n_classes <= 2:
                    newpaths = newpaths.reshape(1, n_folds, n_cs, 1, n_dof)
                else:
                    newpaths = newpaths.reshape(n_classes, n_folds, n_cs, 1, n_dof)
                newscores = newscores.reshape(n_folds, n_cs, 1)
                newniter = newniter.reshape(n_folds, n_cs, 1)
                if self.penalty == "l1":
                    self.l1_ratio_ = 1.0
                else:
                    self.l1_ratio_ = 0.0
            else:
                n_l1_ratios = len(self.l1_ratios_)
                self.l1_ratio_ = float(self.l1_ratio_[0])
                if n_classes <= 2:
                    newpaths = newpaths.reshape(1, n_folds, n_cs, n_l1_ratios, n_dof)
                else:
                    newpaths = newpaths.reshape(
                        n_classes, n_folds, n_cs, n_l1_ratios, n_dof
                    )
            # newpaths.shape = (n_classes, n_folds, n_cs, n_l1_ratios, n_dof)
            # self.coefs_paths_.shape should be
            # (n_folds, n_l1_ratios, n_cs, n_classes, n_dof)
            self.coefs_paths_ = np.moveaxis(newpaths, (0, 1, 3), (3, 0, 1))
            # newscores.shape = (n_folds, n_cs, n_l1_ratios)
            # self.scores_.shape should be (n_folds, n_l1_ratios, n_cs)
            self.scores_ = np.moveaxis(newscores, (1, 2), (2, 1))
            self.n_iter_ = np.moveaxis(newniter, (1, 2), (2, 1))

        return self