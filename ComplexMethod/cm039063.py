def fit(self, X, y, sample_weight=None, **fit_params):
        """Fit the calibrated model.

        Parameters
        ----------
        X : array-like of shape (n_samples, n_features)
            Training data.

        y : array-like of shape (n_samples,)
            Target values.

        sample_weight : array-like of shape (n_samples,), default=None
            Sample weights. If None, then samples are equally weighted.

        **fit_params : dict
            Parameters to pass to the `fit` method of the underlying
            classifier.

        Returns
        -------
        self : object
            Returns an instance of self.
        """
        check_classification_targets(y)
        X, y = indexable(X, y)
        estimator = self._get_estimator()

        _ensemble = self.ensemble
        if _ensemble == "auto":
            _ensemble = not isinstance(estimator, FrozenEstimator)

        self.calibrated_classifiers_ = []

        # Set `classes_` using all `y`
        label_encoder_ = LabelEncoder().fit(y)
        self.classes_ = label_encoder_.classes_
        if self.method == "temperature" and isinstance(y[0], str):
            # for temperature scaling if `y` contains strings then encode it
            # right here to avoid fitting LabelEncoder again within the
            # `_fit_calibrator` function.
            y = label_encoder_.transform(y=y)

        if _routing_enabled():
            routed_params = process_routing(
                self,
                "fit",
                sample_weight=sample_weight,
                **fit_params,
            )
        else:
            # sample_weight checks
            fit_parameters = signature(estimator.fit).parameters
            supports_sw = "sample_weight" in fit_parameters
            if sample_weight is not None and not supports_sw:
                estimator_name = type(estimator).__name__
                warnings.warn(
                    f"Since {estimator_name} does not appear to accept"
                    " sample_weight, sample weights will only be used for the"
                    " calibration itself. This can be caused by a limitation of"
                    " the current scikit-learn API. See the following issue for"
                    " more details:"
                    " https://github.com/scikit-learn/scikit-learn/issues/21134."
                    " Be warned that the result of the calibration is likely to be"
                    " incorrect."
                )
            routed_params = Bunch()
            routed_params.splitter = Bunch(split={})  # no routing for splitter
            routed_params.estimator = Bunch(fit=fit_params)
            if sample_weight is not None and supports_sw:
                routed_params.estimator.fit["sample_weight"] = sample_weight

        xp, is_array_api, device_ = get_namespace_and_device(X)
        if is_array_api:
            y, sample_weight = move_to(y, sample_weight, xp=xp, device=device_)
        # Check that each cross-validation fold can have at least one
        # example per class
        if isinstance(self.cv, int):
            n_folds = self.cv
        elif hasattr(self.cv, "n_splits"):
            n_folds = self.cv.n_splits
        else:
            n_folds = None
        if n_folds and xp.any(xp.unique_counts(y)[1] < n_folds):
            raise ValueError(
                f"Requesting {n_folds}-fold "
                "cross-validation but provided less than "
                f"{n_folds} examples for at least one class."
            )
        if isinstance(self.cv, LeaveOneOut):
            raise ValueError(
                "LeaveOneOut cross-validation does not allow"
                "all classes to be present in test splits. "
                "Please use a cross-validation generator that allows "
                "all classes to appear in every test and train split."
            )
        cv = check_cv(self.cv, y, classifier=True)

        if _ensemble:
            parallel = Parallel(n_jobs=self.n_jobs)
            self.calibrated_classifiers_ = parallel(
                delayed(_fit_classifier_calibrator_pair)(
                    clone(estimator),
                    X,
                    y,
                    train=train,
                    test=test,
                    method=self.method,
                    classes=self.classes_,
                    xp=xp,
                    sample_weight=sample_weight,
                    fit_params=routed_params.estimator.fit,
                )
                for train, test in cv.split(X, y, **routed_params.splitter.split)
            )
        else:
            this_estimator = clone(estimator)
            method_name = _check_response_method(
                this_estimator,
                ["decision_function", "predict_proba"],
            ).__name__
            predictions = cross_val_predict(
                estimator=this_estimator,
                X=X,
                y=y,
                cv=cv,
                method=method_name,
                n_jobs=self.n_jobs,
                params=routed_params.estimator.fit,
            )
            if self.classes_.shape[0] == 2:
                # Ensure shape (n_samples, 1) in the binary case
                if method_name == "predict_proba":
                    # Select the probability column of the positive class
                    predictions = _process_predict_proba(
                        y_pred=predictions,
                        target_type="binary",
                        classes=self.classes_,
                        pos_label=self.classes_[1],
                    )
                predictions = predictions.reshape(-1, 1)

            if sample_weight is not None:
                # Check that the sample_weight dtype is consistent with the
                # predictions to avoid unintentional upcasts.
                sample_weight = _check_sample_weight(
                    sample_weight, predictions, dtype=predictions.dtype
                )

            this_estimator.fit(X, y, **routed_params.estimator.fit)
            # Note: Here we don't pass on fit_params because the supported
            # calibrators don't support fit_params anyway
            calibrated_classifier = _fit_calibrator(
                this_estimator,
                predictions,
                y,
                self.classes_,
                self.method,
                xp=xp,
                sample_weight=sample_weight,
            )
            self.calibrated_classifiers_.append(calibrated_classifier)

        first_clf = self.calibrated_classifiers_[0].estimator
        if hasattr(first_clf, "n_features_in_"):
            self.n_features_in_ = first_clf.n_features_in_
        if hasattr(first_clf, "feature_names_in_"):
            self.feature_names_in_ = first_clf.feature_names_in_
        return self