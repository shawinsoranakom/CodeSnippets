def _dense_fit(self, X, strategy, missing_values, fill_value):
        """Fit the transformer on dense data."""
        missing_mask = _get_mask(X, missing_values)
        masked_X = ma.masked_array(X, mask=missing_mask)

        super()._fit_indicator(missing_mask)

        # Mean
        if strategy == "mean":
            mean_masked = np.ma.mean(masked_X, axis=0)
            # Avoid the warning "Warning: converting a masked element to nan."
            mean = np.ma.getdata(mean_masked)
            mean[np.ma.getmask(mean_masked)] = 0 if self.keep_empty_features else np.nan

            return mean

        # Median
        elif strategy == "median":
            median_masked = np.ma.median(masked_X, axis=0)
            # Avoid the warning "Warning: converting a masked element to nan."
            median = np.ma.getdata(median_masked)
            median[np.ma.getmaskarray(median_masked)] = (
                0 if self.keep_empty_features else np.nan
            )

            return median

        # Most frequent
        elif strategy == "most_frequent":
            # Avoid use of scipy.stats.mstats.mode due to the required
            # additional overhead and slow benchmarking performance.
            # See Issue 14325 and PR 14399 for full discussion.

            # To be able access the elements by columns
            X = X.transpose()
            mask = missing_mask.transpose()

            if X.dtype.kind == "O":
                most_frequent = np.empty(X.shape[0], dtype=object)
            else:
                most_frequent = np.empty(X.shape[0])

            for i, (row, row_mask) in enumerate(zip(X[:], mask[:])):
                row_mask = np.logical_not(row_mask).astype(bool)
                row = row[row_mask]
                if len(row) == 0 and self.keep_empty_features:
                    most_frequent[i] = 0
                else:
                    most_frequent[i] = _most_frequent(row, np.nan, 0)

            return most_frequent

        # Constant
        elif strategy == "constant":
            # for constant strategy, self.statistcs_ is used to store
            # fill_value in each column, or np.nan for columns to drop
            statistics = np.full(X.shape[1], fill_value, dtype=np.object_)

            if not self.keep_empty_features:
                for i in range(missing_mask.shape[1]):
                    if missing_mask[:, i].all():
                        statistics[i] = np.nan

            return statistics

        # Custom
        elif isinstance(strategy, Callable):
            statistics = np.empty(masked_X.shape[1])
            for i in range(masked_X.shape[1]):
                statistics[i] = self.strategy(masked_X[:, i].compressed())
            return statistics