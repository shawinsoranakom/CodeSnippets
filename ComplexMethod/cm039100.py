def fit(self, X, y=None, sample_weight=None):
        """Compute knot positions of splines.

        Parameters
        ----------
        X : array-like of shape (n_samples, n_features)
            The data.

        y : None
            Ignored.

        sample_weight : array-like of shape (n_samples,), default = None
            Individual weights for each sample. Used to calculate quantiles if
            `knots="quantile"`. For `knots="uniform"`, zero weighted
            observations are ignored for finding the min and max of `X`.

        Returns
        -------
        self : object
            Fitted transformer.
        """
        try:
            X = validate_data(
                self,
                X,
                reset=True,
                accept_sparse=False,
                ensure_min_samples=2,
                ensure_2d=True,
                ensure_all_finite=(self.handle_missing != "zeros"),
            )
        except ValueError as e:
            if "Input X contains NaN." in str(e) and self.handle_missing == "error":
                raise ValueError(
                    "Input X contains NaN values and `SplineTransformer` is configured "
                    "to error in this case (handle_missing='error'). To avoid this "
                    "error, set handle_missing='zeros' to encode missing values as "
                    "splines with value 0 or ensure no missing values in X."
                ) from e
            raise e

        if sample_weight is not None:
            sample_weight = _check_sample_weight(sample_weight, X, dtype=X.dtype)

        _, n_features = X.shape

        if isinstance(self.knots, str):
            base_knots = self._get_base_knot_positions(
                X,
                n_knots=self.n_knots,
                knots=self.knots,
                sample_weight=sample_weight,
            )
        else:
            base_knots = check_array(self.knots, dtype=np.float64)
            if base_knots.shape[0] < 2:
                raise ValueError("Number of knots, knots.shape[0], must be >= 2.")
            elif base_knots.shape[1] != n_features:
                raise ValueError("knots.shape[1] == n_features is violated.")
            elif not np.all(np.diff(base_knots, axis=0) > 0):
                raise ValueError("knots must be sorted without duplicates.")

        # number of knots for base interval
        n_knots = base_knots.shape[0]

        if self.extrapolation == "periodic" and n_knots <= self.degree:
            raise ValueError(
                "Periodic splines require degree < n_knots. Got n_knots="
                f"{n_knots} and degree={self.degree}."
            )

        # number of splines basis functions
        if self.extrapolation != "periodic":
            n_splines = n_knots + self.degree - 1
        else:
            # periodic splines have self.degree less degrees of freedom
            n_splines = n_knots - 1

        degree = self.degree
        n_out = n_features * n_splines
        # We have to add degree number of knots below, and degree number knots
        # above the base knots in order to make the spline basis complete.
        if self.extrapolation == "periodic":
            # For periodic splines the spacing of the first / last degree knots
            # needs to be a continuation of the spacing of the last / first
            # base knots.
            period = base_knots[-1] - base_knots[0]
            knots = np.r_[
                base_knots[-(degree + 1) : -1] - period,
                base_knots,
                base_knots[1 : (degree + 1)] + period,
            ]

        else:
            # Eilers & Marx in "Flexible smoothing with B-splines and
            # penalties" https://doi.org/10.1214/ss/1038425655 advice
            # against repeating first and last knot several times, which
            # would have inferior behaviour at boundaries if combined with
            # a penalty (hence P-Spline). We follow this advice even if our
            # splines are unpenalized. Meaning we do not:
            # knots = np.r_[
            #     np.tile(base_knots.min(axis=0), reps=[degree, 1]),
            #     base_knots,
            #     np.tile(base_knots.max(axis=0), reps=[degree, 1])
            # ]
            # Instead, we reuse the distance of the 2 fist/last knots.
            dist_min = base_knots[1] - base_knots[0]
            dist_max = base_knots[-1] - base_knots[-2]

            knots = np.r_[
                np.linspace(
                    base_knots[0] - degree * dist_min,
                    base_knots[0] - dist_min,
                    num=degree,
                ),
                base_knots,
                np.linspace(
                    base_knots[-1] + dist_max,
                    base_knots[-1] + degree * dist_max,
                    num=degree,
                ),
            ]

        # With a diagonal coefficient matrix, we get back the spline basis
        # elements, i.e. the design matrix of the spline.
        # Note, BSpline appreciates C-contiguous float64 arrays as c=coef.
        coef = np.eye(n_splines, dtype=np.float64)
        if self.extrapolation == "periodic":
            coef = np.concatenate((coef, coef[:degree, :]))

        extrapolate = self.extrapolation in ["periodic", "continue"]

        bsplines = [
            BSpline.construct_fast(
                knots[:, i], coef, self.degree, extrapolate=extrapolate
            )
            for i in range(n_features)
        ]
        self.bsplines_ = bsplines

        self.n_features_out_ = n_out - n_features * (1 - self.include_bias)
        return self