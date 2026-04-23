def _check_subparams(self, n_samples, n_features):
        n_subsamples = self.n_subsamples

        if self.fit_intercept:
            n_dim = n_features + 1
        else:
            n_dim = n_features

        if n_subsamples is not None:
            if n_subsamples > n_samples:
                raise ValueError(
                    "Invalid parameter since n_subsamples > "
                    "n_samples ({0} > {1}).".format(n_subsamples, n_samples)
                )
            if n_samples >= n_features:
                if n_dim > n_subsamples:
                    plus_1 = "+1" if self.fit_intercept else ""
                    raise ValueError(
                        "Invalid parameter since n_features{0} "
                        "> n_subsamples ({1} > {2})."
                        "".format(plus_1, n_dim, n_subsamples)
                    )
            else:  # if n_samples < n_features
                if n_subsamples != n_samples:
                    raise ValueError(
                        "Invalid parameter since n_subsamples != "
                        "n_samples ({0} != {1}) while n_samples "
                        "< n_features.".format(n_subsamples, n_samples)
                    )
        else:
            n_subsamples = min(n_dim, n_samples)

        all_combinations = max(1, np.rint(binom(n_samples, n_subsamples)))
        n_subpopulation = int(min(self.max_subpopulation, all_combinations))

        return n_subsamples, n_subpopulation