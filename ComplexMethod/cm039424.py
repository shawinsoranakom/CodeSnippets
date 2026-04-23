def fit(self, X, y, sample_weight=None, monitor=None):
        """Fit the gradient boosting model.

        Parameters
        ----------
        X : {array-like, sparse matrix} of shape (n_samples, n_features)
            The input samples. Internally, it will be converted to
            ``dtype=np.float32`` and if a sparse matrix is provided
            to a sparse ``csr_array``.

        y : array-like of shape (n_samples,)
            Target values (strings or integers in classification, real numbers
            in regression)
            For classification, labels must correspond to classes.

        sample_weight : array-like of shape (n_samples,), default=None
            Sample weights. If None, then samples are equally weighted. Splits
            that would create child nodes with net zero or negative weight are
            ignored while searching for a split in each node. In the case of
            classification, splits are also ignored if they would result in any
            single class carrying a negative weight in either child node.

        monitor : callable, default=None
            The monitor is called after each iteration with the current
            iteration, a reference to the estimator and the local variables of
            ``_fit_stages`` as keyword arguments ``callable(i, self,
            locals())``. If the callable returns ``True`` the fitting procedure
            is stopped. The monitor can be used for various things such as
            computing held-out estimates, early stopping, model introspect, and
            snapshotting.

        Returns
        -------
        self : object
            Fitted estimator.
        """
        if not self.warm_start:
            self._clear_state()

        if self.criterion != "deprecated":
            warnings.warn(
                "The parameter `criterion` is deprecated and will be "
                "removed in 1.11. It has no effect. Leave it to its default value to "
                "avoid this warning.",
                FutureWarning,
            )

        # Check input
        # Since check_array converts both X and y to the same dtype, but the
        # trees use different types for X and y, checking them separately.

        X, y = validate_data(
            self,
            X,
            y,
            accept_sparse=["csr", "csc", "coo"],
            dtype=DTYPE,
            multi_output=True,
        )
        sample_weight_is_none = sample_weight is None
        sample_weight = _check_sample_weight(sample_weight, X)
        if sample_weight_is_none:
            y = self._encode_y(y=y, sample_weight=None)
        else:
            y = self._encode_y(y=y, sample_weight=sample_weight)
        y = column_or_1d(y, warn=True)  # TODO: Is this still required?

        self._set_max_features()

        # self.loss is guaranteed to be a string
        self._loss = self._get_loss(sample_weight=sample_weight)

        if self.n_iter_no_change is not None:
            stratify = y if is_classifier(self) else None
            (
                X_train,
                X_val,
                y_train,
                y_val,
                sample_weight_train,
                sample_weight_val,
            ) = train_test_split(
                X,
                y,
                sample_weight,
                random_state=self.random_state,
                test_size=self.validation_fraction,
                stratify=stratify,
            )
            if is_classifier(self):
                if self.n_classes_ != np.unique(y_train).shape[0]:
                    # We choose to error here. The problem is that the init
                    # estimator would be trained on y, which has some missing
                    # classes now, so its predictions would not have the
                    # correct shape.
                    raise ValueError(
                        "The training data after the early stopping split "
                        "is missing some classes. Try using another random "
                        "seed."
                    )
        else:
            X_train, y_train, sample_weight_train = X, y, sample_weight
            X_val = y_val = sample_weight_val = None

        n_samples = X_train.shape[0]

        # First time calling fit.
        if not self._is_fitted():
            # init state
            self._init_state()

            # fit initial model and initialize raw predictions
            if self.init_ == "zero":
                raw_predictions = np.zeros(
                    shape=(n_samples, self.n_trees_per_iteration_),
                    dtype=np.float64,
                )
            else:
                # XXX clean this once we have a support_sample_weight tag
                if sample_weight_is_none:
                    self.init_.fit(X_train, y_train)
                else:
                    msg = (
                        "The initial estimator {} does not support sample "
                        "weights.".format(self.init_.__class__.__name__)
                    )
                    try:
                        self.init_.fit(
                            X_train, y_train, sample_weight=sample_weight_train
                        )
                    except TypeError as e:
                        if "unexpected keyword argument 'sample_weight'" in str(e):
                            # regular estimator without SW support
                            raise ValueError(msg) from e
                        else:  # regular estimator whose input checking failed
                            raise
                    except ValueError as e:
                        if (
                            "pass parameters to specific steps of "
                            "your pipeline using the "
                            "stepname__parameter" in str(e)
                        ):  # pipeline
                            raise ValueError(msg) from e
                        else:  # regular estimator whose input checking failed
                            raise

                raw_predictions = _init_raw_predictions(
                    X_train, self.init_, self._loss, is_classifier(self)
                )

            begin_at_stage = 0

            # The rng state must be preserved if warm_start is True
            self._rng = check_random_state(self.random_state)

        # warm start: this is not the first time fit was called
        else:
            # add more estimators to fitted model
            # invariant: warm_start = True
            if self.n_estimators < self.estimators_.shape[0]:
                raise ValueError(
                    "n_estimators=%d must be larger or equal to "
                    "estimators_.shape[0]=%d when "
                    "warm_start==True" % (self.n_estimators, self.estimators_.shape[0])
                )
            begin_at_stage = self.estimators_.shape[0]
            # The requirements of _raw_predict
            # are more constrained than fit. It accepts only CSR
            # matrices. Finite values have already been checked in _validate_data.
            X_train = check_array(
                X_train,
                dtype=DTYPE,
                order="C",
                accept_sparse="csr",
                ensure_all_finite=False,
            )
            raw_predictions = self._raw_predict(X_train)
            self._resize_state()

        # fit the boosting stages
        n_stages = self._fit_stages(
            X_train,
            y_train,
            raw_predictions,
            sample_weight_train,
            self._rng,
            X_val,
            y_val,
            sample_weight_val,
            begin_at_stage,
            monitor,
        )

        # change shape of arrays after fit (early-stopping or additional ests)
        if n_stages != self.estimators_.shape[0]:
            self.estimators_ = self.estimators_[:n_stages]
            self.train_score_ = self.train_score_[:n_stages]
            if hasattr(self, "oob_improvement_"):
                # OOB scores were computed
                self.oob_improvement_ = self.oob_improvement_[:n_stages]
                self.oob_scores_ = self.oob_scores_[:n_stages]
                self.oob_score_ = self.oob_scores_[-1]
        self.n_estimators_ = n_stages
        return self