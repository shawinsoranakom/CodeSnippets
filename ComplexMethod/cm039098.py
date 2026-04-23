def fit(self, X, y=None):
        """
        Compute number of output features.

        Parameters
        ----------
        X : {array-like, sparse matrix} of shape (n_samples, n_features)
            The data.

        y : Ignored
            Not used, present here for API consistency by convention.

        Returns
        -------
        self : object
            Fitted transformer.
        """
        _, n_features = validate_data(self, X, accept_sparse=True).shape

        if isinstance(self.degree, Integral):
            if self.degree == 0 and not self.include_bias:
                raise ValueError(
                    "Setting degree to zero and include_bias to False would result in"
                    " an empty output array."
                )

            self._min_degree = 0
            self._max_degree = self.degree
        elif (
            isinstance(self.degree, collections.abc.Iterable) and len(self.degree) == 2
        ):
            self._min_degree, self._max_degree = self.degree
            if not (
                isinstance(self._min_degree, Integral)
                and isinstance(self._max_degree, Integral)
                and self._min_degree >= 0
                and self._min_degree <= self._max_degree
            ):
                raise ValueError(
                    "degree=(min_degree, max_degree) must "
                    "be non-negative integers that fulfil "
                    "min_degree <= max_degree, got "
                    f"{self.degree}."
                )
            elif self._max_degree == 0 and not self.include_bias:
                raise ValueError(
                    "Setting both min_degree and max_degree to zero and include_bias to"
                    " False would result in an empty output array."
                )
        else:
            raise ValueError(
                "degree must be a non-negative int or tuple "
                "(min_degree, max_degree), got "
                f"{self.degree}."
            )

        self.n_output_features_ = self._num_combinations(
            n_features=n_features,
            min_degree=self._min_degree,
            max_degree=self._max_degree,
            interaction_only=self.interaction_only,
            include_bias=self.include_bias,
        )
        if self.n_output_features_ > np.iinfo(np.intp).max:
            msg = (
                "The output that would result from the current configuration would"
                f" have {self.n_output_features_} features which is too large to be"
                f" indexed by {np.intp().dtype.name}. Please change some or all of the"
                " following:\n- The number of features in the input, currently"
                f" {n_features=}\n- The range of degrees to calculate, currently"
                f" [{self._min_degree}, {self._max_degree}]\n- Whether to include only"
                f" interaction terms, currently {self.interaction_only}\n- Whether to"
                f" include a bias term, currently {self.include_bias}."
            )
            if (
                np.intp == np.int32
                and self.n_output_features_ <= np.iinfo(np.int64).max
            ):  # pragma: nocover
                msg += (
                    "\nNote that the current Python runtime has a limited 32 bit "
                    "address space and that this configuration would have been "
                    "admissible if run on a 64 bit Python runtime."
                )
            raise ValueError(msg)
        # We also record the number of output features for
        # _min_degree = 0
        self._n_out_full = self._num_combinations(
            n_features=n_features,
            min_degree=0,
            max_degree=self._max_degree,
            interaction_only=self.interaction_only,
            include_bias=self.include_bias,
        )

        return self