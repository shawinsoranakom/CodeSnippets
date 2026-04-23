def _check_input_parameters(self, X, y, split_params):
        # We need to enforce that successive calls to cv.split() yield the same
        # splits: see https://github.com/scikit-learn/scikit-learn/issues/15149
        if not _yields_constant_splits(self._checked_cv_orig):
            raise ValueError(
                "The cv parameter must yield consistent folds across "
                "calls to split(). Set its random_state to an int, or set "
                "shuffle=False."
            )

        if (
            self.resource != "n_samples"
            and self.resource not in self.estimator.get_params()
        ):
            raise ValueError(
                f"Cannot use resource={self.resource} which is not supported "
                f"by estimator {self.estimator.__class__.__name__}"
            )

        if isinstance(self, HalvingRandomSearchCV):
            if self.min_resources == self.n_candidates == "exhaust":
                # for n_candidates=exhaust to work, we need to know what
                # min_resources is. Similarly min_resources=exhaust needs to
                # know the actual number of candidates.
                raise ValueError(
                    "n_candidates and min_resources cannot be both set to 'exhaust'."
                )

        self.min_resources_ = self.min_resources
        if self.min_resources_ in ("smallest", "exhaust"):
            if self.resource == "n_samples":
                n_splits = self._checked_cv_orig.get_n_splits(X, y, **split_params)
                # please see https://gph.is/1KjihQe for a justification
                magic_factor = 2
                self.min_resources_ = n_splits * magic_factor
                if is_classifier(self.estimator):
                    y = validate_data(self, X="no_validation", y=y)
                    check_classification_targets(y)
                    n_classes = np.unique(y).shape[0]
                    self.min_resources_ *= n_classes
            else:
                self.min_resources_ = 1
            # if 'exhaust', min_resources_ might be set to a higher value later
            # in _run_search

        self.max_resources_ = self.max_resources
        if self.max_resources_ == "auto":
            if not self.resource == "n_samples":
                raise ValueError(
                    "resource can only be 'n_samples' when max_resources='auto'"
                )
            self.max_resources_ = _num_samples(X)

        if self.min_resources_ > self.max_resources_:
            raise ValueError(
                f"min_resources_={self.min_resources_} is greater "
                f"than max_resources_={self.max_resources_}."
            )

        if self.min_resources_ == 0:
            raise ValueError(
                f"min_resources_={self.min_resources_}: you might have passed "
                "an empty dataset X."
            )