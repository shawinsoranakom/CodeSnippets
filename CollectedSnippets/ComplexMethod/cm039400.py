def _fit(self, X, y=None):
        ensure_all_finite = "allow-nan" if get_tags(self).input_tags.allow_nan else True
        if self.__sklearn_tags__().target_tags.required:
            if not isinstance(X, (KDTree, BallTree, NeighborsBase)):
                X, y = validate_data(
                    self,
                    X,
                    y,
                    accept_sparse="csr",
                    multi_output=True,
                    order="C",
                    ensure_all_finite=ensure_all_finite,
                )

            if is_classifier(self):
                # Classification targets require a specific format
                if y.ndim == 1 or (y.ndim == 2 and y.shape[1] == 1):
                    if y.ndim != 1:
                        warnings.warn(
                            (
                                "A column-vector y was passed when a "
                                "1d array was expected. Please change "
                                "the shape of y to (n_samples,), for "
                                "example using ravel()."
                            ),
                            DataConversionWarning,
                            stacklevel=2,
                        )

                    self.outputs_2d_ = False
                    y = y.reshape((-1, 1))
                else:
                    self.outputs_2d_ = True

                check_classification_targets(y)
                self.classes_ = []
                # Using `dtype=np.intp` is necessary since `np.bincount`
                # (called in _classification.py) fails when dealing
                # with a float64 array on 32bit systems.
                self._y = np.empty(y.shape, dtype=np.intp)
                for k in range(self._y.shape[1]):
                    classes, self._y[:, k] = np.unique(y[:, k], return_inverse=True)
                    self.classes_.append(classes)

                if not self.outputs_2d_:
                    self.classes_ = self.classes_[0]
                    self._y = self._y.ravel()
            else:
                self._y = y

        else:
            if not isinstance(X, (KDTree, BallTree, NeighborsBase)):
                X = validate_data(
                    self,
                    X,
                    ensure_all_finite=ensure_all_finite,
                    accept_sparse="csr",
                    order="C",
                )

        self._check_algorithm_metric()
        if self.metric_params is None:
            self.effective_metric_params_ = {}
        else:
            self.effective_metric_params_ = self.metric_params.copy()

        effective_p = self.effective_metric_params_.get("p", self.p)
        if self.metric == "minkowski":
            self.effective_metric_params_["p"] = effective_p

        self.effective_metric_ = self.metric
        # For minkowski distance, use more efficient methods where available
        if self.metric == "minkowski":
            p = self.effective_metric_params_.pop("p", 2)
            w = self.effective_metric_params_.pop("w", None)

            if p == 1 and w is None:
                self.effective_metric_ = "manhattan"
            elif p == 2 and w is None:
                self.effective_metric_ = "euclidean"
            elif p == np.inf and w is None:
                self.effective_metric_ = "chebyshev"
            else:
                # Use the generic minkowski metric, possibly weighted.
                self.effective_metric_params_["p"] = p
                self.effective_metric_params_["w"] = w

        if isinstance(X, NeighborsBase):
            self._fit_X = X._fit_X
            self._tree = X._tree
            self._fit_method = X._fit_method
            self.n_samples_fit_ = X.n_samples_fit_
            return self

        elif isinstance(X, BallTree):
            self._fit_X = X.data
            self._tree = X
            self._fit_method = "ball_tree"
            self.n_samples_fit_ = X.data.shape[0]
            return self

        elif isinstance(X, KDTree):
            self._fit_X = X.data
            self._tree = X
            self._fit_method = "kd_tree"
            self.n_samples_fit_ = X.data.shape[0]
            return self

        if self.metric == "precomputed":
            X = _check_precomputed(X)
            # Precomputed matrix X must be squared
            if X.shape[0] != X.shape[1]:
                raise ValueError(
                    "Precomputed matrix must be square."
                    " Input is a {}x{} matrix.".format(X.shape[0], X.shape[1])
                )
            self.n_features_in_ = X.shape[1]

        n_samples = X.shape[0]
        if n_samples == 0:
            raise ValueError("n_samples must be greater than 0")

        if issparse(X):
            if self.algorithm not in ("auto", "brute"):
                warnings.warn("cannot use tree with sparse input: using brute force")

            if (
                self.effective_metric_ not in VALID_METRICS_SPARSE["brute"]
                and not callable(self.effective_metric_)
                and not isinstance(self.effective_metric_, DistanceMetric)
            ):
                raise ValueError(
                    "Metric '%s' not valid for sparse input. "
                    "Use sorted(sklearn.neighbors."
                    "VALID_METRICS_SPARSE['brute']) "
                    "to get valid options. "
                    "Metric can also be a callable function." % (self.effective_metric_)
                )
            self._fit_X = X.copy()
            self._tree = None
            self._fit_method = "brute"
            self.n_samples_fit_ = X.shape[0]
            return self

        self._fit_method = self.algorithm
        self._fit_X = X
        self.n_samples_fit_ = X.shape[0]

        if self._fit_method == "auto":
            # A tree approach is better for small number of neighbors or small
            # number of features, with KDTree generally faster when available
            if (
                self.metric == "precomputed"
                or self._fit_X.shape[1] > 15
                or (
                    self.n_neighbors is not None
                    and self.n_neighbors >= self._fit_X.shape[0] // 2
                )
            ):
                self._fit_method = "brute"
            else:
                if (
                    self.effective_metric_ == "minkowski"
                    and self.effective_metric_params_["p"] < 1
                ):
                    self._fit_method = "brute"
                elif (
                    self.effective_metric_ == "minkowski"
                    and self.effective_metric_params_.get("w") is not None
                ):
                    # 'minkowski' with weights is not supported by KDTree but is
                    # supported byBallTree.
                    self._fit_method = "ball_tree"
                elif self.effective_metric_ in VALID_METRICS["kd_tree"]:
                    self._fit_method = "kd_tree"
                elif (
                    callable(self.effective_metric_)
                    or self.effective_metric_ in VALID_METRICS["ball_tree"]
                ):
                    self._fit_method = "ball_tree"
                else:
                    self._fit_method = "brute"

        if (
            self.effective_metric_ == "minkowski"
            and self.effective_metric_params_["p"] < 1
        ):
            # For 0 < p < 1 Minkowski distances aren't valid distance
            # metric as they do not satisfy triangular inequality:
            # they are semi-metrics.
            # algorithm="kd_tree" and algorithm="ball_tree" can't be used because
            # KDTree and BallTree require a proper distance metric to work properly.
            # However, the brute-force algorithm supports semi-metrics.
            if self._fit_method == "brute":
                warnings.warn(
                    "Mind that for 0 < p < 1, Minkowski metrics are not distance"
                    " metrics. Continuing the execution with `algorithm='brute'`."
                )
            else:  # self._fit_method in ("kd_tree", "ball_tree")
                raise ValueError(
                    f'algorithm="{self._fit_method}" does not support 0 < p < 1 for '
                    "the Minkowski metric. To resolve this problem either "
                    'set p >= 1 or algorithm="brute".'
                )

        if self._fit_method == "ball_tree":
            self._tree = BallTree(
                X,
                self.leaf_size,
                metric=self.effective_metric_,
                **self.effective_metric_params_,
            )
        elif self._fit_method == "kd_tree":
            if (
                self.effective_metric_ == "minkowski"
                and self.effective_metric_params_.get("w") is not None
            ):
                raise ValueError(
                    "algorithm='kd_tree' is not valid for "
                    "metric='minkowski' with a weight parameter 'w': "
                    "try algorithm='ball_tree' "
                    "or algorithm='brute' instead."
                )
            self._tree = KDTree(
                X,
                self.leaf_size,
                metric=self.effective_metric_,
                **self.effective_metric_params_,
            )
        elif self._fit_method == "brute":
            self._tree = None

        return self