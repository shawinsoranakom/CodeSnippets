def _sparse_fit(self, X, strategy, missing_values, fill_value):
        """Fit the transformer on sparse data."""
        missing_mask = _get_mask(X, missing_values)
        mask_data = missing_mask.data
        n_implicit_zeros = X.shape[0] - np.diff(X.indptr)

        statistics = np.empty(X.shape[1])

        if strategy == "constant":
            # for constant strategy, self.statistics_ is used to store
            # fill_value in each column, or np.nan for columns to drop
            statistics.fill(fill_value)

            if not self.keep_empty_features:
                if SCIPY_VERSION_BELOW_1_12:
                    for i in range(missing_mask.shape[1]):
                        if all(missing_mask[:, [i]].data):
                            statistics[i] = np.nan
                else:
                    for i in range(missing_mask.shape[1]):
                        if all(missing_mask[:, i].data):
                            statistics[i] = np.nan

        else:
            for i in range(X.shape[1]):
                column = X.data[X.indptr[i] : X.indptr[i + 1]]
                mask_column = mask_data[X.indptr[i] : X.indptr[i + 1]]
                column = column[~mask_column]

                # combine explicit and implicit zeros
                mask_zeros = _get_mask(column, 0)
                column = column[~mask_zeros]
                n_explicit_zeros = mask_zeros.sum()
                n_zeros = n_implicit_zeros[i] + n_explicit_zeros

                if len(column) == 0 and self.keep_empty_features:
                    # in case we want to keep columns with only missing values.
                    statistics[i] = 0
                else:
                    if strategy == "mean":
                        s = column.size + n_zeros
                        statistics[i] = np.nan if s == 0 else column.sum() / s

                    elif strategy == "median":
                        statistics[i] = _get_median(column, n_zeros)

                    elif strategy == "most_frequent":
                        statistics[i] = _most_frequent(column, 0, n_zeros)

                    elif isinstance(strategy, Callable):
                        statistics[i] = self.strategy(column)

        super()._fit_indicator(missing_mask)

        return statistics