def fit_transform(self, X, y, **params):
        """Fit :class:`TargetEncoder` and transform `X` with the target encoding.

        This method uses a :term:`cross fitting` scheme to prevent target leakage
        and overfitting in downstream predictors. It is the recommended method for
        encoding training data.

        .. note::
            `fit(X, y).transform(X)` does not equal `fit_transform(X, y)` because a
            :term:`cross fitting` scheme is used in `fit_transform` for encoding.
            See the :ref:`User Guide <target_encoder>` for details.

        Parameters
        ----------
        X : array-like of shape (n_samples, n_features)
            The data to determine the categories of each feature.

        y : array-like of shape (n_samples,)
            The target data used to encode the categories.

        **params : dict
            Parameters to route to the internal CV object.

            Can only be used in conjunction with a cross-validation generator as CV
            object.

            For instance, `groups` (array-like of shape `(n_samples,)`) can be routed to
            a CV splitter that accepts `groups`, such as :class:`GroupKFold` or
            :class:`StratifiedGroupKFold`.

            .. versionadded:: 1.9
                Only available if `enable_metadata_routing=True`, which can be
                set by using ``sklearn.set_config(enable_metadata_routing=True)``.
                See :ref:`Metadata Routing User Guide <metadata_routing>` for
                more details.

        Returns
        -------
        X_trans : ndarray of shape (n_samples, n_features) or \
                    (n_samples, (n_features * n_classes))
            Transformed input.
        """
        # avoid circular imports
        from sklearn.model_selection import (
            GroupKFold,
            KFold,
            StratifiedGroupKFold,
            StratifiedKFold,
        )
        from sklearn.model_selection._split import check_cv

        _raise_for_params(params, self, "fit_transform")

        X_ordinal, X_known_mask, y_encoded, n_categories = self._fit_encodings_all(X, y)

        # TODO(1.11): remove code block
        if self.shuffle != "deprecated" or self.random_state != "deprecated":
            warnings.warn(
                "`TargetEncoder.shuffle` and `TargetEncoder.random_state` are "
                "deprecated in version 1.9 and will be removed in version 1.11. Pass a "
                "cross-validation generator as `cv` argument to specify the shuffling "
                "behaviour instead.",
                FutureWarning,
            )
        shuffle = True if self.shuffle == "deprecated" else self.shuffle
        cv_kwargs = {"shuffle": shuffle}
        if self.random_state != "deprecated":
            cv_kwargs["random_state"] = self.random_state

        # TODO(1.11): pass shuffle=True to keep backwards compatibility for default
        # inputs (will be ignored in `check_cv` if a cv object is passed);
        # `random_state` already defaults to `None` in `check_cv` and doesn't need to
        # be passed here
        cv = check_cv(
            self.cv,
            y,
            classifier=self.target_type_ != "continuous",
            **cv_kwargs,
        )

        if _routing_enabled():
            if params["groups"] is not None:
                X, y, params["groups"] = indexable(X, y, params["groups"])
            routed_params = process_routing(self, "fit_transform", **params)
        else:
            routed_params = Bunch(splitter=Bunch(split={}))

        # The internal cross-fitting is only well-defined when each sample index
        # appears in exactly one validation fold. Skip the validation check for
        # known non-overlapping splitters in scikit-learn:
        if not isinstance(
            cv, (GroupKFold, KFold, StratifiedKFold, StratifiedGroupKFold)
        ):
            seen_count = np.zeros(X.shape[0])
            for _, test_idx in cv.split(X, y, **routed_params.splitter.split):
                seen_count[test_idx] += 1
            if not np.all(seen_count == 1):
                raise ValueError(
                    "Validation indices from `cv` must cover each sample index exactly "
                    "once with no overlap. Pass a splitter with non-overlapping "
                    "validation folds as `cv` or refer to the docs for other options."
                )

        # If 'multiclass' multiply axis=1 by num classes else keep shape the same
        if self.target_type_ == "multiclass":
            X_out = np.empty(
                (X_ordinal.shape[0], X_ordinal.shape[1] * len(self.classes_)),
                dtype=np.float64,
            )
        else:
            X_out = np.empty_like(X_ordinal, dtype=np.float64)

        for train_idx, test_idx in cv.split(X, y, **routed_params.splitter.split):
            X_train, y_train = X_ordinal[train_idx, :], y_encoded[train_idx]
            y_train_mean = np.mean(y_train, axis=0)

            if self.target_type_ == "multiclass":
                encodings = self._fit_encoding_multiclass(
                    X_train,
                    y_train,
                    n_categories,
                    y_train_mean,
                )
            else:
                encodings = self._fit_encoding_binary_or_continuous(
                    X_train,
                    y_train,
                    n_categories,
                    y_train_mean,
                )
            self._transform_X_ordinal(
                X_out,
                X_ordinal,
                ~X_known_mask,
                test_idx,
                encodings,
                y_train_mean,
            )
        return X_out