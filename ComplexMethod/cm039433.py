def fit(
        self,
        X,
        y,
        sample_weight=None,
        *,
        X_val=None,
        y_val=None,
        sample_weight_val=None,
    ):
        """Fit the gradient boosting model.

        Parameters
        ----------
        X : array-like of shape (n_samples, n_features)
            The input samples.

        y : array-like of shape (n_samples,)
            Target values.

        sample_weight : array-like of shape (n_samples,) default=None
            Weights of training data.

            .. versionadded:: 0.23

        X_val : array-like of shape (n_val, n_features)
            Additional sample of features for validation used in early stopping.
            In a `Pipeline`, `X_val` can be transformed the same way as `X` with
            `Pipeline(..., transform_input=["X_val"])`.

            .. versionadded:: 1.7

        y_val : array-like of shape (n_samples,)
            Additional sample of target values for validation used in early stopping.

            .. versionadded:: 1.7

        sample_weight_val : array-like of shape (n_samples,) default=None
            Additional weights for validation used in early stopping.

            .. versionadded:: 1.7

        Returns
        -------
        self : object
            Fitted estimator.
        """
        fit_start_time = time()
        acc_find_split_time = 0.0  # time spent finding the best splits
        acc_apply_split_time = 0.0  # time spent splitting nodes
        acc_compute_hist_time = 0.0  # time spent computing histograms
        # time spent predicting X for gradient and hessians update
        acc_prediction_time = 0.0
        X, known_categories = self._preprocess_X(X, reset=True)
        y = _check_y(y, estimator=self)
        y = self._encode_y(y)
        check_consistent_length(X, y)
        # Do not create unit sample weights by default to later skip some
        # computation
        if sample_weight is not None:
            sample_weight = _check_sample_weight(sample_weight, X, dtype=np.float64)
            # TODO: remove when PDP supports sample weights
            self._fitted_with_sw = True

        sample_weight = self._finalize_sample_weight(sample_weight, y)

        validation_data_provided = X_val is not None or y_val is not None
        if validation_data_provided:
            if y_val is None:
                raise ValueError("X_val is provided, but y_val was not provided.")
            if X_val is None:
                raise ValueError("y_val is provided, but X_val was not provided.")
            X_val = self._preprocess_X(X_val, reset=False)
            y_val = _check_y(y_val, estimator=self)
            y_val = self._encode_y_val(y_val)
            check_consistent_length(X_val, y_val)
            if sample_weight_val is not None:
                sample_weight_val = _check_sample_weight(
                    sample_weight_val, X_val, dtype=np.float64
                )
            if self.early_stopping is False:
                raise ValueError(
                    "X_val and y_val are passed to fit while at the same time "
                    "early_stopping is False. When passing X_val and y_val to fit,"
                    "early_stopping should be set to either 'auto' or True."
                )

        # Note: At this point, we could delete self._label_encoder if it exists.
        # But we don't to keep the code even simpler.

        rng = check_random_state(self.random_state)

        # When warm starting, we want to reuse the same seed that was used
        # the first time fit was called (e.g. train/val split).
        # For feature subsampling, we want to continue with the rng we started with.
        if not self.warm_start or not self._is_fitted():
            self._random_seed = rng.randint(np.iinfo(np.uint32).max, dtype="u8")
            feature_subsample_seed = rng.randint(np.iinfo(np.uint32).max, dtype="u8")
            self._feature_subsample_rng = np.random.default_rng(feature_subsample_seed)

        self._validate_parameters()
        monotonic_cst = _check_monotonic_cst(self, self.monotonic_cst)
        # _preprocess_X places the categorical features at the beginning,
        # change the order of monotonic_cst accordingly
        if self.is_categorical_ is not None:
            monotonic_cst_remapped = np.concatenate(
                (
                    monotonic_cst[self.is_categorical_],
                    monotonic_cst[~self.is_categorical_],
                )
            )
        else:
            monotonic_cst_remapped = monotonic_cst

        # used for validation in predict
        n_samples, self._n_features = X.shape

        # Encode constraints into a list of sets of features indices (integers).
        interaction_cst = self._check_interaction_cst(self._n_features)

        # we need this stateful variable to tell raw_predict() that it was
        # called from fit() (this current method), and that the data it has
        # received is pre-binned.
        # predicting is faster on pre-binned data, so we want early stopping
        # predictions to be made on pre-binned data. Unfortunately the _scorer
        # can only call predict() or predict_proba(), not raw_predict(), and
        # there's no way to tell the scorer that it needs to predict binned
        # data.
        self._in_fit = True

        # `_openmp_effective_n_threads` is used to take cgroups CPU quotes
        # into account when determine the maximum number of threads to use.
        n_threads = _openmp_effective_n_threads()

        if isinstance(self.loss, str):
            self._loss = self._get_loss(sample_weight=sample_weight)
        elif isinstance(self.loss, BaseLoss):
            self._loss = self.loss

        if self.early_stopping == "auto":
            self.do_early_stopping_ = n_samples > 10_000
        else:
            self.do_early_stopping_ = self.early_stopping

        # create validation data if needed
        self._use_validation_data = (
            self.validation_fraction is not None or validation_data_provided
        )
        if (
            self.do_early_stopping_
            and self._use_validation_data
            and not validation_data_provided
        ):
            # stratify for classification
            # instead of checking predict_proba, loss.n_classes >= 2 would also work
            stratify = y if hasattr(self._loss, "predict_proba") else None

            # Save the state of the RNG for the training and validation split.
            # This is needed in order to have the same split when using
            # warm starting.

            if sample_weight is None:
                X_train, X_val, y_train, y_val = train_test_split(
                    X,
                    y,
                    test_size=self.validation_fraction,
                    stratify=stratify,
                    random_state=self._random_seed,
                )
                sample_weight_train = sample_weight_val = None
            else:
                # TODO: incorporate sample_weight in sampling here, as well as
                # stratify
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
                    test_size=self.validation_fraction,
                    stratify=stratify,
                    random_state=self._random_seed,
                )
        else:
            X_train, y_train, sample_weight_train = X, y, sample_weight
            if not validation_data_provided:
                X_val = y_val = sample_weight_val = None

        # Bin the data
        # For ease of use of the API, the user-facing GBDT classes accept the
        # parameter max_bins, which doesn't take into account the bin for
        # missing values (which is always allocated). However, since max_bins
        # isn't the true maximal number of bins, all other private classes
        # (binmapper, histbuilder...) accept n_bins instead, which is the
        # actual total number of bins. Everywhere in the code, the
        # convention is that n_bins == max_bins + 1
        n_bins = self.max_bins + 1  # + 1 for missing values
        self._bin_mapper = _BinMapper(
            n_bins=n_bins,
            is_categorical=self._is_categorical_remapped,
            known_categories=known_categories,
            random_state=self._random_seed,
            n_threads=n_threads,
        )
        X_binned_train = self._bin_data(
            X_train, sample_weight_train, is_training_data=True
        )
        if X_val is not None:
            X_binned_val = self._bin_data(
                X_val, sample_weight_val, is_training_data=False
            )
        else:
            X_binned_val = None

        # Uses binned data to check for missing values
        has_missing_values = (
            (X_binned_train == self._bin_mapper.missing_values_bin_idx_)
            .any(axis=0)
            .astype(np.uint8)
        )

        if self.verbose:
            print("Fitting gradient boosted rounds:")

        n_samples = X_binned_train.shape[0]
        scoring_is_predefined_string = self.scoring in _SCORERS
        need_raw_predictions_val = X_binned_val is not None and (
            scoring_is_predefined_string or self.scoring == "loss"
        )
        # First time calling fit, or no warm start
        if not (self._is_fitted() and self.warm_start):
            # Clear random state and score attributes
            self._clear_state()

            # initialize raw_predictions: those are the accumulated values
            # predicted by the trees for the training data. raw_predictions has
            # shape (n_samples, n_trees_per_iteration) where
            # n_trees_per_iterations is n_classes in multiclass classification,
            # else 1.
            # self._baseline_prediction has shape (1, n_trees_per_iteration)
            self._baseline_prediction = self._loss.fit_intercept_only(
                y_true=y_train, sample_weight=sample_weight_train
            ).reshape((1, -1))
            raw_predictions = np.zeros(
                shape=(n_samples, self.n_trees_per_iteration_),
                dtype=self._baseline_prediction.dtype,
                order="F",
            )
            raw_predictions += self._baseline_prediction

            # predictors is a matrix (list of lists) of TreePredictor objects
            # with shape (n_iter_, n_trees_per_iteration)
            self._predictors = predictors = []

            # Initialize structures and attributes related to early stopping
            self._scorer = None  # set if scoring != loss
            raw_predictions_val = None  # set if use val and scoring is a string
            self.train_score_ = []
            self.validation_score_ = []

            if self.do_early_stopping_:
                # populate train_score and validation_score with the
                # predictions of the initial model (before the first tree)

                # Create raw_predictions_val for storing the raw predictions of
                # the validation data.
                if need_raw_predictions_val:
                    raw_predictions_val = np.zeros(
                        shape=(X_binned_val.shape[0], self.n_trees_per_iteration_),
                        dtype=self._baseline_prediction.dtype,
                        order="F",
                    )

                    raw_predictions_val += self._baseline_prediction

                if self.scoring == "loss":
                    # we're going to compute scoring w.r.t the loss. As losses
                    # take raw predictions as input (unlike the scorers), we
                    # can optimize a bit and avoid repeating computing the
                    # predictions of the previous trees. We'll reuse
                    # raw_predictions (as it's needed for training anyway) for
                    # evaluating the training loss.

                    self._check_early_stopping_loss(
                        raw_predictions=raw_predictions,
                        y_train=y_train,
                        sample_weight_train=sample_weight_train,
                        raw_predictions_val=raw_predictions_val,
                        y_val=y_val,
                        sample_weight_val=sample_weight_val,
                        n_threads=n_threads,
                    )
                else:
                    self._scorer = check_scoring(self, self.scoring)
                    # _scorer is a callable with signature (est, X, y) and
                    # calls est.predict() or est.predict_proba() depending on
                    # its nature.
                    # Unfortunately, each call to _scorer() will compute
                    # the predictions of all the trees. So we use a subset of
                    # the training set to compute train scores.

                    # Compute the subsample set
                    (
                        X_binned_small_train,
                        y_small_train,
                        sample_weight_small_train,
                        indices_small_train,
                    ) = self._get_small_trainset(
                        X_binned_train,
                        y_train,
                        sample_weight_train,
                        self._random_seed,
                    )

                    # If the scorer is a predefined string, then we optimize
                    # the evaluation by reusing the incrementally updated raw
                    # predictions.
                    if scoring_is_predefined_string:
                        raw_predictions_small_train = raw_predictions[
                            indices_small_train
                        ]
                    else:
                        raw_predictions_small_train = None

                    self._check_early_stopping_scorer(
                        X_binned_small_train,
                        y_small_train,
                        sample_weight_small_train,
                        X_binned_val,
                        y_val,
                        sample_weight_val,
                        raw_predictions_small_train=raw_predictions_small_train,
                        raw_predictions_val=raw_predictions_val,
                    )
            begin_at_stage = 0

        # warm start: this is not the first time fit was called
        else:
            # Check that the maximum number of iterations is not smaller
            # than the number of iterations from the previous fit
            if self.max_iter < self.n_iter_:
                raise ValueError(
                    "max_iter=%d must be larger than or equal to "
                    "n_iter_=%d when warm_start==True" % (self.max_iter, self.n_iter_)
                )

            # Convert array attributes to lists
            self.train_score_ = self.train_score_.tolist()
            self.validation_score_ = self.validation_score_.tolist()

            # Compute raw predictions
            raw_predictions = self._raw_predict(X_binned_train, n_threads=n_threads)
            if self.do_early_stopping_ and need_raw_predictions_val:
                raw_predictions_val = self._raw_predict(
                    X_binned_val, n_threads=n_threads
                )
            else:
                raw_predictions_val = None

            if self.do_early_stopping_ and self.scoring != "loss":
                # Compute the subsample set
                (
                    X_binned_small_train,
                    y_small_train,
                    sample_weight_small_train,
                    indices_small_train,
                ) = self._get_small_trainset(
                    X_binned_train, y_train, sample_weight_train, self._random_seed
                )

            # Get the predictors from the previous fit
            predictors = self._predictors

            begin_at_stage = self.n_iter_

        # initialize gradients and hessians (empty arrays).
        # shape = (n_samples, n_trees_per_iteration).
        gradient, hessian = self._loss.init_gradient_and_hessian(
            n_samples=n_samples, dtype=G_H_DTYPE, order="F"
        )

        for iteration in range(begin_at_stage, self.max_iter):
            if self.verbose >= 2:
                iteration_start_time = time()
                print(
                    "[{}/{}] ".format(iteration + 1, self.max_iter), end="", flush=True
                )

            # Update gradients and hessians, inplace
            # Note that self._loss expects shape (n_samples,) for
            # n_trees_per_iteration = 1 else shape (n_samples, n_trees_per_iteration).
            if self._loss.constant_hessian:
                self._loss.gradient(
                    y_true=y_train,
                    raw_prediction=raw_predictions,
                    sample_weight=sample_weight_train,
                    gradient_out=gradient,
                    n_threads=n_threads,
                )
            else:
                self._loss.gradient_hessian(
                    y_true=y_train,
                    raw_prediction=raw_predictions,
                    sample_weight=sample_weight_train,
                    gradient_out=gradient,
                    hessian_out=hessian,
                    n_threads=n_threads,
                )

            # Append a list since there may be more than 1 predictor per iter
            predictors.append([])

            # 2-d views of shape (n_samples, n_trees_per_iteration_) or (n_samples, 1)
            # on gradient and hessian to simplify the loop over n_trees_per_iteration_.
            if gradient.ndim == 1:
                g_view = gradient.reshape((-1, 1))
                h_view = hessian.reshape((-1, 1))
            else:
                g_view = gradient
                h_view = hessian

            # Build `n_trees_per_iteration` trees.
            for k in range(self.n_trees_per_iteration_):
                grower = TreeGrower(
                    X_binned=X_binned_train,
                    gradients=g_view[:, k],
                    hessians=h_view[:, k],
                    n_bins=n_bins,
                    n_bins_non_missing=self._bin_mapper.n_bins_non_missing_,
                    has_missing_values=has_missing_values,
                    is_categorical=self._is_categorical_remapped,
                    monotonic_cst=monotonic_cst_remapped,
                    interaction_cst=interaction_cst,
                    max_leaf_nodes=self.max_leaf_nodes,
                    max_depth=self.max_depth,
                    min_samples_leaf=self.min_samples_leaf,
                    l2_regularization=self.l2_regularization,
                    feature_fraction_per_split=self.max_features,
                    rng=self._feature_subsample_rng,
                    shrinkage=self.learning_rate,
                    n_threads=n_threads,
                )
                grower.grow()

                acc_apply_split_time += grower.total_apply_split_time
                acc_find_split_time += grower.total_find_split_time
                acc_compute_hist_time += grower.total_compute_hist_time

                if not self._loss.differentiable:
                    _update_leaves_values(
                        loss=self._loss,
                        grower=grower,
                        y_true=y_train,
                        raw_prediction=raw_predictions[:, k],
                        sample_weight=sample_weight_train,
                    )

                predictor = grower.make_predictor(
                    binning_thresholds=self._bin_mapper.bin_thresholds_
                )
                predictors[-1].append(predictor)

                # Update raw_predictions with the predictions of the newly
                # created tree.
                tic_pred = time()
                _update_raw_predictions(raw_predictions[:, k], grower, n_threads)
                toc_pred = time()
                acc_prediction_time += toc_pred - tic_pred

            should_early_stop = False
            if self.do_early_stopping_:
                # Update raw_predictions_val with the newest tree(s)
                if need_raw_predictions_val:
                    for k, pred in enumerate(self._predictors[-1]):
                        raw_predictions_val[:, k] += pred.predict_binned(
                            X_binned_val,
                            self._bin_mapper.missing_values_bin_idx_,
                            n_threads,
                        )

                if self.scoring == "loss":
                    should_early_stop = self._check_early_stopping_loss(
                        raw_predictions=raw_predictions,
                        y_train=y_train,
                        sample_weight_train=sample_weight_train,
                        raw_predictions_val=raw_predictions_val,
                        y_val=y_val,
                        sample_weight_val=sample_weight_val,
                        n_threads=n_threads,
                    )

                else:
                    # If the scorer is a predefined string, then we optimize the
                    # evaluation by reusing the incrementally computed raw predictions.
                    if scoring_is_predefined_string:
                        raw_predictions_small_train = raw_predictions[
                            indices_small_train
                        ]
                    else:
                        raw_predictions_small_train = None

                    should_early_stop = self._check_early_stopping_scorer(
                        X_binned_small_train,
                        y_small_train,
                        sample_weight_small_train,
                        X_binned_val,
                        y_val,
                        sample_weight_val,
                        raw_predictions_small_train=raw_predictions_small_train,
                        raw_predictions_val=raw_predictions_val,
                    )

            if self.verbose >= 2:
                self._print_iteration_stats(iteration_start_time)

            # maybe we could also early stop if all the trees are stumps?
            if should_early_stop:
                break

        if self.verbose:
            duration = time() - fit_start_time
            n_total_leaves = sum(
                predictor.get_n_leaf_nodes()
                for predictors_at_ith_iteration in self._predictors
                for predictor in predictors_at_ith_iteration
            )
            n_predictors = sum(
                len(predictors_at_ith_iteration)
                for predictors_at_ith_iteration in self._predictors
            )
            print(
                "Fit {} trees in {:.3f} s, ({} total leaves)".format(
                    n_predictors, duration, n_total_leaves
                )
            )
            print(
                "{:<32} {:.3f}s".format(
                    "Time spent computing histograms:", acc_compute_hist_time
                )
            )
            print(
                "{:<32} {:.3f}s".format(
                    "Time spent finding best splits:", acc_find_split_time
                )
            )
            print(
                "{:<32} {:.3f}s".format(
                    "Time spent applying splits:", acc_apply_split_time
                )
            )
            print(
                "{:<32} {:.3f}s".format("Time spent predicting:", acc_prediction_time)
            )

        self.train_score_ = np.asarray(self.train_score_)
        self.validation_score_ = np.asarray(self.validation_score_)
        del self._in_fit  # hard delete so we're sure it can't be used anymore
        return self