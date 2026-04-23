def _fit(self, X, y, step_score=None, **fit_params):
        # Parameter step_score controls the calculation of self.step_scores_
        # step_score is not exposed to users and is used when implementing RFECV
        # self.step_scores_ will not be calculated when calling _fit through fit

        X, y = validate_data(
            self,
            X,
            y,
            accept_sparse="csc",
            ensure_min_features=2,
            ensure_all_finite=False,
            multi_output=True,
        )

        # Initialization
        n_features = X.shape[1]
        if self.n_features_to_select is None:
            n_features_to_select = n_features // 2
        elif isinstance(self.n_features_to_select, Integral):  # int
            n_features_to_select = self.n_features_to_select
            if n_features_to_select > n_features:
                warnings.warn(
                    (
                        f"Found {n_features_to_select=} > {n_features=}. There will be"
                        " no feature selection and all features will be kept."
                    ),
                    UserWarning,
                )
        else:  # float
            n_features_to_select = int(n_features * self.n_features_to_select)

        if 0.0 < self.step < 1.0:
            step = int(max(1, self.step * n_features))
        else:
            step = int(self.step)

        support_ = np.ones(n_features, dtype=bool)
        ranking_ = np.ones(n_features, dtype=int)

        if step_score:
            self.step_n_features_ = []
            self.step_scores_ = []
            self.step_support_ = []
            self.step_ranking_ = []

        # Elimination
        while np.sum(support_) > n_features_to_select:
            # Remaining features
            features = np.arange(n_features)[support_]

            # Rank the remaining features
            estimator = clone(self.estimator)
            if self.verbose > 0:
                print("Fitting estimator with %d features." % np.sum(support_))

            estimator.fit(X[:, features], y, **fit_params)

            # Compute step values on the previous selection iteration because
            # 'estimator' must use features that have not been eliminated yet
            if step_score:
                self.step_n_features_.append(len(features))
                self.step_scores_.append(step_score(estimator, features))
                self.step_support_.append(list(support_))
                self.step_ranking_.append(list(ranking_))

            # Get importance and rank them
            importances = _get_feature_importances(
                estimator,
                self.importance_getter,
                transform_func="square",
            )
            ranks = np.argsort(importances, kind="stable")

            # for sparse case ranks is matrix
            ranks = np.ravel(ranks)

            # Eliminate the worse features
            threshold = min(step, np.sum(support_) - n_features_to_select)

            support_[features[ranks][:threshold]] = False
            ranking_[np.logical_not(support_)] += 1

        # Set final attributes
        features = np.arange(n_features)[support_]
        self.estimator_ = clone(self.estimator)
        self.estimator_.fit(X[:, features], y, **fit_params)

        # Compute step values when only n_features_to_select features left
        if step_score:
            self.step_n_features_.append(len(features))
            self.step_scores_.append(step_score(self.estimator_, features))
            self.step_support_.append(support_)
            self.step_ranking_.append(ranking_)
        self.n_features_ = support_.sum()
        self.support_ = support_
        self.ranking_ = ranking_

        return self