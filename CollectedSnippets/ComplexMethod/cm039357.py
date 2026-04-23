def _validate_input(self, X, in_fit):
        if self.strategy in ("most_frequent", "constant"):
            # If input is a list of strings, dtype = object.
            # Otherwise ValueError is raised in SimpleImputer
            # with strategy='most_frequent' or 'constant'
            # because the list is converted to Unicode numpy array
            if isinstance(X, list) and any(
                isinstance(elem, str) for row in X for elem in row
            ):
                dtype = object
            else:
                dtype = None
        else:
            dtype = FLOAT_DTYPES

        if not in_fit and self._fit_dtype.kind == "O":
            # Use object dtype if fitted on object dtypes
            dtype = self._fit_dtype

        if is_pandas_na(self.missing_values) or is_scalar_nan(self.missing_values):
            ensure_all_finite = "allow-nan"
        else:
            ensure_all_finite = True

        try:
            X = validate_data(
                self,
                X,
                reset=in_fit,
                accept_sparse="csc",
                dtype=dtype,
                force_writeable=True if not in_fit else None,
                ensure_all_finite=ensure_all_finite,
                copy=self.copy,
            )
        except ValueError as ve:
            if "could not convert" in str(ve):
                new_ve = ValueError(
                    "Cannot use {} strategy with non-numeric data:\n{}".format(
                        self.strategy, ve
                    )
                )
                raise new_ve from None
            else:
                raise ve

        if in_fit:
            # Use the dtype seen in `fit` for non-`fit` conversion
            self._fit_dtype = X.dtype

        _check_inputs_dtype(X, self.missing_values)
        if X.dtype.kind not in ("i", "u", "f", "O"):
            raise ValueError(
                "SimpleImputer does not support data with dtype "
                "{0}. Please provide either a numeric array (with"
                " a floating point or integer dtype) or "
                "categorical data represented either as an array "
                "with integer dtype or an array of string values "
                "with an object dtype.".format(X.dtype)
            )

        if sp.issparse(X) and self.missing_values == 0:
            # missing_values = 0 not allowed with sparse data as it would
            # force densification
            raise ValueError(
                "Imputation not possible when missing_values "
                "== 0 and input is sparse. Provide a dense "
                "array instead."
            )

        if self.strategy == "constant":
            if in_fit and self.fill_value is not None:
                fill_value_dtype = type(self.fill_value)
                err_msg = (
                    f"fill_value={self.fill_value!r} (of type {fill_value_dtype!r}) "
                    f"cannot be cast to the input data that is {X.dtype!r}. "
                    "If fill_value is a Python scalar, instead pass  a numpy scalar "
                    "(e.g. fill_value=np.uint8(0) if your data is of type np.uint8). "
                    "Make sure that both dtypes are of the same kind."
                )
            elif not in_fit:
                fill_value_dtype = self._fill_dtype
                err_msg = (
                    f"The dtype of the filling value (i.e. {fill_value_dtype!r}) "
                    f"cannot be cast to the input data that is {X.dtype!r}. "
                    "Make sure that the dtypes of the input data are of the same kind "
                    "between fit and transform."
                )
            else:
                # By default, fill_value=None, and the replacement is always
                # compatible with the input data
                fill_value_dtype = X.dtype

            # Make sure we can safely cast fill_value dtype to the input data dtype
            if not np.can_cast(fill_value_dtype, X.dtype, casting="same_kind"):
                raise ValueError(err_msg)

        return X