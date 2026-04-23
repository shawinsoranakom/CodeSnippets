def _fit(
        self,
        X,
        y,
        sample_weight=None,
        check_input=True,
        missing_values_in_feature_mask=None,
    ):
        random_state = check_random_state(self.random_state)

        if check_input:
            # Need to validate separately here.
            # We can't pass multi_output=True because that would allow y to be
            # csr.

            # _compute_missing_values_in_feature_mask will check for finite values and
            # compute the missing mask if the tree supports missing values
            check_X_params = dict(
                dtype=DTYPE, accept_sparse="csc", ensure_all_finite=False
            )
            check_y_params = dict(ensure_2d=False, dtype=None)
            X, y = validate_data(
                self, X, y, validate_separately=(check_X_params, check_y_params)
            )

            missing_values_in_feature_mask = (
                self._compute_missing_values_in_feature_mask(X)
            )
            if issparse(X):
                X.sort_indices()

                if X.indices.dtype != np.intc or X.indptr.dtype != np.intc:
                    raise ValueError(
                        "No support for np.int64 index based sparse matrices"
                    )

            if self.criterion == "poisson":
                if np.any(y < 0):
                    raise ValueError(
                        "Some value(s) of y are negative which is"
                        " not allowed for Poisson regression."
                    )
                if np.sum(y) <= 0:
                    raise ValueError(
                        "Sum of y is not positive which is "
                        "necessary for Poisson regression."
                    )

        # Determine output settings
        n_samples, self.n_features_in_ = X.shape
        is_classification = is_classifier(self)

        y = np.atleast_1d(y)
        expanded_class_weight = None

        if y.ndim == 1:
            # reshape is necessary to preserve the data contiguity against vs
            # [:, np.newaxis] that does not.
            y = np.reshape(y, (-1, 1))

        self.n_outputs_ = y.shape[1]

        if is_classification:
            check_classification_targets(y)
            y = np.copy(y)

            self.classes_ = []
            self.n_classes_ = []

            if self.class_weight is not None:
                y_original = np.copy(y)

            y_encoded = np.zeros(y.shape, dtype=int)
            for k in range(self.n_outputs_):
                classes_k, y_encoded[:, k] = np.unique(y[:, k], return_inverse=True)
                self.classes_.append(classes_k)
                self.n_classes_.append(classes_k.shape[0])
            y = y_encoded

            if self.class_weight is not None:
                expanded_class_weight = compute_sample_weight(
                    self.class_weight, y_original
                )

            self.n_classes_ = np.array(self.n_classes_, dtype=np.intp)

        if getattr(y, "dtype", None) != DOUBLE or not y.flags.contiguous:
            y = np.ascontiguousarray(y, dtype=DOUBLE)

        max_depth = np.iinfo(np.int32).max if self.max_depth is None else self.max_depth

        if isinstance(self.min_samples_leaf, numbers.Integral):
            min_samples_leaf = self.min_samples_leaf
        else:  # float
            min_samples_leaf = ceil(self.min_samples_leaf * n_samples)

        if isinstance(self.min_samples_split, numbers.Integral):
            min_samples_split = self.min_samples_split
        else:  # float
            min_samples_split = ceil(self.min_samples_split * n_samples)
            min_samples_split = max(2, min_samples_split)

        min_samples_split = max(min_samples_split, 2 * min_samples_leaf)

        if isinstance(self.max_features, str):
            if self.max_features == "sqrt":
                max_features = max(1, int(np.sqrt(self.n_features_in_)))
            elif self.max_features == "log2":
                max_features = max(1, int(np.log2(self.n_features_in_)))
        elif self.max_features is None:
            max_features = self.n_features_in_
        elif isinstance(self.max_features, numbers.Integral):
            max_features = self.max_features
        else:  # float
            if self.max_features > 0.0:
                max_features = max(1, int(self.max_features * self.n_features_in_))
            else:
                max_features = 0

        self.max_features_ = max_features

        max_leaf_nodes = -1 if self.max_leaf_nodes is None else self.max_leaf_nodes

        if len(y) != n_samples:
            raise ValueError(
                "Number of labels=%d does not match number of samples=%d"
                % (len(y), n_samples)
            )

        if sample_weight is not None:
            sample_weight = _check_sample_weight(sample_weight, X, dtype=DOUBLE)

        if expanded_class_weight is not None:
            if sample_weight is not None:
                sample_weight = sample_weight * expanded_class_weight
            else:
                sample_weight = expanded_class_weight

        # Set min_weight_leaf from min_weight_fraction_leaf
        if sample_weight is None:
            min_weight_leaf = self.min_weight_fraction_leaf * n_samples
        else:
            min_weight_leaf = self.min_weight_fraction_leaf * np.sum(sample_weight)

        # Build tree
        criterion = self.criterion
        if not isinstance(criterion, Criterion):
            if is_classification:
                criterion = CRITERIA_CLF[self.criterion](
                    self.n_outputs_, self.n_classes_
                )
            else:
                criterion = CRITERIA_REG[self.criterion](self.n_outputs_, n_samples)
        else:
            # Make a deepcopy in case the criterion has mutable attributes that
            # might be shared and modified concurrently during parallel fitting
            criterion = copy.deepcopy(criterion)

        SPLITTERS = SPARSE_SPLITTERS if issparse(X) else DENSE_SPLITTERS

        splitter = self.splitter
        if self.monotonic_cst is None:
            monotonic_cst = None
        else:
            if self.n_outputs_ > 1:
                raise ValueError(
                    "Monotonicity constraints are not supported with multiple outputs."
                )
            # Check to correct monotonicity constraint' specification,
            # by applying element-wise logical conjunction
            # Note: we do not cast `np.asarray(self.monotonic_cst, dtype=np.int8)`
            # straight away here so as to generate error messages for invalid
            # values using the original values prior to any dtype related conversion.
            monotonic_cst = np.asarray(self.monotonic_cst)
            if monotonic_cst.shape[0] != X.shape[1]:
                raise ValueError(
                    "monotonic_cst has shape {} but the input data "
                    "X has {} features.".format(monotonic_cst.shape[0], X.shape[1])
                )
            valid_constraints = np.isin(monotonic_cst, (-1, 0, 1))
            if not np.all(valid_constraints):
                unique_constaints_value = np.unique(monotonic_cst)
                raise ValueError(
                    "monotonic_cst must be None or an array-like of -1, 0 or 1, but"
                    f" got {unique_constaints_value}"
                )
            monotonic_cst = np.asarray(monotonic_cst, dtype=np.int8)
            if is_classifier(self):
                if self.n_classes_[0] > 2:
                    raise ValueError(
                        "Monotonicity constraints are not supported with multiclass "
                        "classification"
                    )
                # Binary classification trees are built by constraining probabilities
                # of the *negative class* in order to make the implementation similar
                # to regression trees.
                # Since self.monotonic_cst encodes constraints on probabilities of the
                # *positive class*, all signs must be flipped.
                monotonic_cst *= -1

        if not isinstance(self.splitter, Splitter):
            splitter = SPLITTERS[self.splitter](
                criterion,
                self.max_features_,
                min_samples_leaf,
                min_weight_leaf,
                random_state,
                monotonic_cst,
            )

        if is_classifier(self):
            self.tree_ = Tree(self.n_features_in_, self.n_classes_, self.n_outputs_)
        else:
            self.tree_ = Tree(
                self.n_features_in_,
                # TODO: tree shouldn't need this in this case
                np.array([1] * self.n_outputs_, dtype=np.intp),
                self.n_outputs_,
            )

        # Use BestFirst if max_leaf_nodes given; use DepthFirst otherwise
        if max_leaf_nodes < 0:
            builder = DepthFirstTreeBuilder(
                splitter,
                min_samples_split,
                min_samples_leaf,
                min_weight_leaf,
                max_depth,
                self.min_impurity_decrease,
            )
        else:
            builder = BestFirstTreeBuilder(
                splitter,
                min_samples_split,
                min_samples_leaf,
                min_weight_leaf,
                max_depth,
                max_leaf_nodes,
                self.min_impurity_decrease,
            )

        builder.build(self.tree_, X, y, sample_weight, missing_values_in_feature_mask)

        if self.n_outputs_ == 1 and is_classifier(self):
            self.n_classes_ = self.n_classes_[0]
            self.classes_ = self.classes_[0]

        self._prune_tree()

        return self