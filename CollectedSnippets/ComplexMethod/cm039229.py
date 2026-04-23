def _call_func_on_transformers(self, X, y, func, column_as_labels, routed_params):
        """
        Private function to fit and/or transform on demand.

        Parameters
        ----------
        X : {array-like, dataframe} of shape (n_samples, n_features)
            The data to be used in fit and/or transform.

        y : array-like of shape (n_samples,)
            Targets.

        func : callable
            Function to call, which can be _fit_transform_one or
            _transform_one.

        column_as_labels : bool
            Used to iterate through transformers. If True, columns are returned
            as strings. If False, columns are returned as they were given by
            the user. Can be True only if the ``ColumnTransformer`` is already
            fitted.

        routed_params : dict
            The routed parameters as the output from ``process_routing``.

        Returns
        -------
        Return value (transformers and/or transformed X data) depends
        on the passed function.
        """
        if func is _fit_transform_one:
            fitted = False
        else:  # func is _transform_one
            fitted = True

        transformers = list(
            self._iter(
                fitted=fitted,
                column_as_labels=column_as_labels,
                skip_drop=True,
                skip_empty_columns=True,
            )
        )
        try:
            jobs = []
            for idx, (name, trans, columns, weight) in enumerate(transformers, start=1):
                if func is _fit_transform_one:
                    if trans == "passthrough":
                        output_config = _get_output_config("transform", self)
                        trans = FunctionTransformer(
                            accept_sparse=True,
                            check_inverse=False,
                            feature_names_out="one-to-one",
                        ).set_output(transform=output_config["dense"])

                    extra_args = dict(
                        message_clsname="ColumnTransformer",
                        message=self._log_message(name, idx, len(transformers)),
                    )
                else:  # func is _transform_one
                    extra_args = {}
                jobs.append(
                    delayed(func)(
                        transformer=clone(trans) if not fitted else trans,
                        X=_safe_indexing(X, columns, axis=1),
                        y=y,
                        weight=weight,
                        **extra_args,
                        params=routed_params[name],
                    )
                )

            return Parallel(n_jobs=self.n_jobs)(jobs)

        except ValueError as e:
            if "Expected 2D array, got 1D array instead" in str(e):
                raise ValueError(_ERR_MSG_1DCOLUMN) from e
            else:
                raise