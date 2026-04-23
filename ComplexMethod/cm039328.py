def partial_fit(self, X, y=None, **partial_fit_params):
        """Fit the SelectFromModel meta-transformer only once.

        Parameters
        ----------
        X : array-like of shape (n_samples, n_features)
            The training input samples.

        y : array-like of shape (n_samples,), default=None
            The target values (integers that correspond to classes in
            classification, real numbers in regression).

        **partial_fit_params : dict
            - If `enable_metadata_routing=False` (default): Parameters directly passed
              to the `partial_fit` method of the sub-estimator.

            - If `enable_metadata_routing=True`: Parameters passed to the `partial_fit`
              method of the sub-estimator. They are ignored if `prefit=True`.

            .. versionchanged:: 1.4

                `**partial_fit_params` are routed to the sub-estimator, if
                `enable_metadata_routing=True` is set via
                :func:`~sklearn.set_config`, which allows for aliasing.

                See :ref:`Metadata Routing User Guide <metadata_routing>` for
                more details.

        Returns
        -------
        self : object
            Fitted estimator.
        """
        first_call = not hasattr(self, "estimator_")

        if first_call:
            self._check_max_features(X)

        if self.prefit:
            if first_call:
                try:
                    check_is_fitted(self.estimator)
                except NotFittedError as exc:
                    raise NotFittedError(
                        "When `prefit=True`, `estimator` is expected to be a fitted "
                        "estimator."
                    ) from exc
                self.estimator_ = deepcopy(self.estimator)
            return self

        if first_call:
            self.estimator_ = clone(self.estimator)
        if _routing_enabled():
            routed_params = process_routing(self, "partial_fit", **partial_fit_params)
            self.estimator_ = clone(self.estimator)
            self.estimator_.partial_fit(X, y, **routed_params.estimator.partial_fit)
        else:
            # TODO(SLEP6): remove when metadata routing cannot be disabled.
            self.estimator_.partial_fit(X, y, **partial_fit_params)

        if hasattr(self.estimator_, "feature_names_in_"):
            self.feature_names_in_ = self.estimator_.feature_names_in_
        else:
            _check_feature_names(self, X, reset=first_call)

        return self