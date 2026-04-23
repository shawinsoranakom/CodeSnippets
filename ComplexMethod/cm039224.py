def fit(self, X, y, **fit_params):
        """Fit the model according to the given training data.

        Parameters
        ----------
        X : {array-like, sparse matrix} of shape (n_samples, n_features)
            Training vector, where `n_samples` is the number of samples and
            `n_features` is the number of features.

        y : array-like of shape (n_samples,)
            Target values.

        **fit_params : dict
            - If `enable_metadata_routing=False` (default): Parameters directly passed
              to the `fit` method of the underlying regressor.

            - If `enable_metadata_routing=True`: Parameters safely routed to the `fit`
              method of the underlying regressor.

            .. versionchanged:: 1.6
                See :ref:`Metadata Routing User Guide <metadata_routing>` for
                more details.

        Returns
        -------
        self : object
            Fitted estimator.
        """
        if y is None:
            raise ValueError(
                f"This {self.__class__.__name__} estimator "
                "requires y to be passed, but the target y is None."
            )
        y = check_array(
            y,
            input_name="y",
            accept_sparse=False,
            ensure_all_finite=True,
            ensure_2d=False,
            dtype="numeric",
            allow_nd=True,
        )

        # store the number of dimension of the target to predict an array of
        # similar shape at predict
        self._training_dim = y.ndim

        # transformers are designed to modify X which is 2d dimensional, we
        # need to modify y accordingly.
        if y.ndim == 1:
            y_2d = y.reshape(-1, 1)
        else:
            y_2d = y
        self._fit_transformer(y_2d)

        # transform y and convert back to 1d array if needed
        y_trans = self.transformer_.transform(y_2d)
        # FIXME: a FunctionTransformer can return a 1D array even when validate
        # is set to True. Therefore, we need to check the number of dimension
        # first.
        if y_trans.ndim == 2 and y_trans.shape[1] == 1 and self._training_dim == 1:
            y_trans = y_trans.squeeze(axis=1)

        self.regressor_ = self._get_regressor(get_clone=True)
        if _routing_enabled():
            routed_params = process_routing(self, "fit", **fit_params)
        else:
            routed_params = Bunch(regressor=Bunch(fit=fit_params))

        self.regressor_.fit(X, y_trans, **routed_params.regressor.fit)

        if hasattr(self.regressor_, "feature_names_in_"):
            self.feature_names_in_ = self.regressor_.feature_names_in_

        return self