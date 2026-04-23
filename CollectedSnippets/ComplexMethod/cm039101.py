def transform(self, X):
        """Transform each feature data to B-splines.

        Parameters
        ----------
        X : array-like of shape (n_samples, n_features)
            The data to transform.

        Returns
        -------
        XBS : {ndarray, sparse matrix} of shape (n_samples, n_features * n_splines)
            The matrix of features, where n_splines is the number of bases
            elements of the B-splines, n_knots + degree - 1.
        """
        check_is_fitted(self)

        X = validate_data(
            self,
            X,
            reset=False,
            accept_sparse=False,
            ensure_2d=True,
            ensure_all_finite=(self.handle_missing != "zeros"),
        )

        n_samples, n_features = X.shape
        n_splines = self.bsplines_[0].c.shape[1]
        degree = self.degree

        # Note that scipy BSpline returns float64 arrays and converts input
        # x=X[:, i] to c-contiguous float64.
        n_out = self.n_features_out_ + n_features * (1 - self.include_bias)
        if X.dtype in FLOAT_DTYPES:
            dtype = X.dtype
        else:
            dtype = np.float64
        if self.sparse_output:
            output_list = []
        else:
            XBS = np.zeros((n_samples, n_out), dtype=dtype, order=self.order)

        for feature_idx in range(n_features):
            spl = self.bsplines_[feature_idx]
            # Get indicator for nan values in the current column.
            nan_row_indices = np.flatnonzero(_get_mask(X[:, feature_idx], np.nan))

            if self.extrapolation in ("continue", "error", "periodic"):
                if self.extrapolation == "periodic":
                    # With periodic extrapolation we map x to the segment
                    # [spl.t[k], spl.t[n]].
                    # This is equivalent to BSpline(.., extrapolate="periodic")
                    # for scipy>=1.0.0.
                    n = spl.t.size - spl.k - 1
                    if spl.t[n] - spl.t[spl.k] > 0:
                        # Assign to new array to avoid inplace operation
                        x = spl.t[spl.k] + (X[:, feature_idx] - spl.t[spl.k]) % (
                            spl.t[n] - spl.t[spl.k]
                        )
                    else:
                        # This can happen if the column has a single non-nan
                        # value. Treat as a constant feature.
                        x = np.zeros_like(X[:, feature_idx])
                else:  # self.extrapolation in ("continue", "error")
                    x = X[:, feature_idx]

                if self.sparse_output:
                    # We replace the nan values in the input column by some
                    # arbitrary, in-range, numerical value since
                    # BSpline.design_matrix() would otherwise raise on any nan
                    # value in its input. The spline encoded values in
                    # the output of that function that correspond to missing
                    # values in the original input will be replaced by 0.0
                    # afterwards.
                    #
                    # Note that in the following we use np.nanmin(x) as the
                    # input replacement to make sure that this code works even
                    # when `extrapolation == "error"`. Any other choice of
                    # in-range value would have worked work since the
                    # corresponding values in the array are replaced by zeros.
                    if nan_row_indices.size == x.size:
                        # The column is all np.nan valued. Replace it by a
                        # constant column with an arbitrary non-nan value
                        # inside so that it is encoded as constant column.
                        x = np.zeros_like(x)  # avoid mutation of input data
                    elif nan_row_indices.shape[0] > 0:
                        x = x.copy()  # avoid mutation of input data
                        x[nan_row_indices] = np.nanmin(x)

                    # Note: self.bsplines_[0].extrapolate is True for extrapolation in
                    # ["periodic", "continue"]
                    XBS_sparse = BSpline.design_matrix(
                        x, spl.t, spl.k, self.bsplines_[0].extrapolate
                    )

                    if self.extrapolation == "periodic":
                        # See the construction of coef in fit. We need to add the last
                        # degree spline basis function to the first degree ones and
                        # then drop the last ones.
                        # Note: See comment about SparseEfficiencyWarning below.
                        XBS_sparse = XBS_sparse.tolil()
                        XBS_sparse[:, :degree] += XBS_sparse[:, -degree:]
                        XBS_sparse = XBS_sparse[:, :-degree]

                    if nan_row_indices.shape[0] > 0:
                        # Note: See comment about SparseEfficiencyWarning below.
                        XBS = XBS_sparse.tolil()

                else:
                    XBS[
                        :, (feature_idx * n_splines) : ((feature_idx + 1) * n_splines)
                    ] = spl(x)

                # Replace any indicated values with 0:
                if nan_row_indices.shape[0] > 0:
                    for spline_idx in range(n_splines):
                        output_feature_idx = n_splines * feature_idx + spline_idx
                        XBS[
                            nan_row_indices, output_feature_idx : output_feature_idx + 1
                        ] = 0
                    if self.sparse_output:
                        XBS_sparse = XBS

            else:  # extrapolation in ("constant", "linear")
                xmin, xmax = spl.t[degree], spl.t[-degree - 1]
                # spline values at boundaries
                f_min, f_max = spl(xmin), spl(xmax)
                # Values outside of the feature range during fit and nan values get
                # filtered out:
                inside_range_mask = (xmin <= X[:, feature_idx]) & (
                    X[:, feature_idx] <= xmax
                )

                if self.sparse_output:
                    outside_range_mask = ~inside_range_mask
                    x = X[:, feature_idx].copy()
                    # Set to some arbitrary value within the range of values
                    # observed on the training set before calling
                    # BSpline.design_matrix. Those transformed will be
                    # reassigned later when handling with extrapolation.
                    x[outside_range_mask] = xmin
                    XBS_sparse = BSpline.design_matrix(x, spl.t, spl.k)
                    # Note: Without converting to lil_matrix we would get:
                    # scipy.sparse._base.SparseEfficiencyWarning: Changing the sparsity
                    # structure of CSC is expensive. LIL is more efficient.
                    if np.any(outside_range_mask):
                        XBS_sparse = XBS_sparse.tolil()
                        XBS_sparse[outside_range_mask, :] = 0

                else:
                    XBS[
                        inside_range_mask,
                        (feature_idx * n_splines) : ((feature_idx + 1) * n_splines),
                    ] = spl(X[inside_range_mask, feature_idx])

            # Note for extrapolation:
            # 'continue' is already returned as is by scipy BSplines
            if self.extrapolation == "error":
                has_nan_output_values = False
                if self.sparse_output:
                    # Early convert to CSR as the sparsity structure of this
                    # block should not change anymore. This is needed to be able
                    # to safely assume that `.data` is a 1D array.
                    XBS_sparse = XBS_sparse.tocsr()
                    has_nan_output_values = np.any(np.isnan(XBS_sparse.data))
                else:
                    output_features = slice(
                        feature_idx * n_splines, (feature_idx + 1) * n_splines
                    )
                    has_nan_output_values = np.any(np.isnan(XBS[:, output_features]))

                if has_nan_output_values:
                    raise ValueError(
                        "`X` contains values beyond the limits of the knots."
                    )

            elif self.extrapolation == "constant":
                # Set all values beyond xmin and xmax to the value of the
                # spline basis functions at those two positions.
                # Only the first degree and last degree number of splines
                # have non-zero values at the boundaries.

                below_xmin_mask = X[:, feature_idx] < xmin
                if np.any(below_xmin_mask):
                    if self.sparse_output:
                        # Note: See comment about SparseEfficiencyWarning above.
                        XBS_sparse = XBS_sparse.tolil()
                        XBS_sparse[below_xmin_mask, :degree] = f_min[:degree]

                    else:
                        XBS[
                            below_xmin_mask,
                            (feature_idx * n_splines) : (
                                feature_idx * n_splines + degree
                            ),
                        ] = f_min[:degree]

                above_xmax_mask = X[:, feature_idx] > xmax
                if np.any(above_xmax_mask):
                    if self.sparse_output:
                        # Note: See comment about SparseEfficiencyWarning above.
                        XBS_sparse = XBS_sparse.tolil()
                        XBS_sparse[above_xmax_mask, -degree:] = f_max[-degree:]
                    else:
                        XBS[
                            above_xmax_mask,
                            ((feature_idx + 1) * n_splines - degree) : (
                                (feature_idx + 1) * n_splines
                            ),
                        ] = f_max[-degree:]

            elif self.extrapolation == "linear":
                # Continue the degree first and degree last spline bases
                # linearly beyond the boundaries, with slope = derivative at
                # the boundary.
                # Note that all others have derivative = value = 0 at the
                # boundaries.

                # spline derivatives = slopes at boundaries
                fp_min, fp_max = spl(xmin, nu=1), spl(xmax, nu=1)
                # Compute the linear continuation.
                if degree <= 1:
                    # For degree=1, the derivative of 2nd spline is not zero at
                    # boundary. For degree=0 it is the same as 'constant'.
                    degree += 1
                for j in range(degree):
                    below_xmin_mask = X[:, feature_idx] < xmin
                    if np.any(below_xmin_mask):
                        linear_extr = (
                            f_min[j]
                            + (X[below_xmin_mask, feature_idx] - xmin) * fp_min[j]
                        )
                        if self.sparse_output:
                            # Note: See comment about SparseEfficiencyWarning above.
                            XBS_sparse = XBS_sparse.tolil()
                            XBS_sparse[below_xmin_mask, j] = linear_extr
                        else:
                            XBS[below_xmin_mask, feature_idx * n_splines + j] = (
                                linear_extr
                            )

                    above_xmax_mask = X[:, feature_idx] > xmax
                    if np.any(above_xmax_mask):
                        k = n_splines - 1 - j
                        linear_extr = (
                            f_max[k]
                            + (X[above_xmax_mask, feature_idx] - xmax) * fp_max[k]
                        )
                        if self.sparse_output:
                            # Note: See comment about SparseEfficiencyWarning above.
                            XBS_sparse = XBS_sparse.tolil()
                            XBS_sparse[above_xmax_mask, k : k + 1] = linear_extr[
                                :, None
                            ]
                        else:
                            XBS[above_xmax_mask, feature_idx * n_splines + k] = (
                                linear_extr
                            )

            if self.sparse_output:
                XBS_sparse = XBS_sparse.tocsr()
                output_list.append(XBS_sparse)

        if self.sparse_output:
            XBS = sparse.hstack(output_list, format="csr")

        XBS = _align_api_if_sparse(XBS)

        if self.include_bias:
            return XBS
        else:
            # We throw away one spline basis per feature.
            # We chose the last one.
            indices = [j for j in range(XBS.shape[1]) if (j + 1) % n_splines != 0]
            return XBS[:, indices]