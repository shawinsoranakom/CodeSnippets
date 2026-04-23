def transform(self, X):
        """Impute all missing values in `X`.

        Parameters
        ----------
        X : {array-like, sparse matrix}, shape (n_samples, n_features)
            The input data to complete.

        Returns
        -------
        X_imputed : {ndarray, sparse matrix} of shape \
                (n_samples, n_features_out)
            `X` with imputed values.
        """
        check_is_fitted(self)

        X = self._validate_input(X, in_fit=False)
        statistics = self.statistics_

        if X.shape[1] != statistics.shape[0]:
            raise ValueError(
                "X has %d features per sample, expected %d"
                % (X.shape[1], self.statistics_.shape[0])
            )

        # compute mask before eliminating invalid features
        missing_mask = _get_mask(X, self.missing_values)

        # Decide whether to keep missing features
        if self.keep_empty_features:
            valid_statistics = statistics.astype(self._fill_dtype, copy=False)
            valid_statistics_indexes = None
        else:
            # same as np.isnan but also works for object dtypes
            invalid_mask = _get_mask(statistics, np.nan)
            valid_mask = np.logical_not(invalid_mask)
            valid_statistics = statistics[valid_mask].astype(
                self._fill_dtype, copy=False
            )
            valid_statistics_indexes = np.flatnonzero(valid_mask)

            if invalid_mask.any():
                invalid_features = np.arange(X.shape[1])[invalid_mask]
                # use feature names warning if features are provided
                if hasattr(self, "feature_names_in_"):
                    invalid_features = self.feature_names_in_[invalid_features]
                warnings.warn(
                    "Skipping features without any observed values:"
                    f" {invalid_features}. At least one non-missing value is needed"
                    f" for imputation with strategy='{self.strategy}'."
                )
                X = X[:, valid_statistics_indexes]

        # Do actual imputation
        if sp.issparse(X):
            if self.missing_values == 0:
                raise ValueError(
                    "Imputation not possible when missing_values "
                    "== 0 and input is sparse. Provide a dense "
                    "array instead."
                )
            else:
                # if no invalid statistics are found, use the mask computed
                # before, else recompute mask
                if valid_statistics_indexes is None:
                    mask = missing_mask.data
                else:
                    mask = _get_mask(X.data, self.missing_values)
                indexes = np.repeat(
                    np.arange(len(X.indptr) - 1, dtype=int), np.diff(X.indptr)
                )[mask]

                X.data[mask] = valid_statistics[indexes]
        else:
            # use mask computed before eliminating invalid mask
            if valid_statistics_indexes is None:
                mask_valid_features = missing_mask
            else:
                mask_valid_features = missing_mask[:, valid_statistics_indexes]
            n_missing = np.sum(mask_valid_features, axis=0)
            values = np.repeat(valid_statistics, n_missing)
            coordinates = np.where(mask_valid_features.transpose())[::-1]

            X[coordinates] = values

        X_indicator = super()._transform_indicator(missing_mask)

        return super()._concatenate_indicator(X, X_indicator)