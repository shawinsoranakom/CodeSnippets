def _fit_transformer(self, y):
        """Check transformer and fit transformer.

        Create the default transformer, fit it and make additional inverse
        check on a subset (optional).

        """
        if self.transformer is not None and (
            self.func is not None or self.inverse_func is not None
        ):
            raise ValueError(
                "'transformer' and functions 'func'/'inverse_func' cannot both be set."
            )
        elif self.transformer is not None:
            self.transformer_ = clone(self.transformer)
        else:
            if (self.func is not None and self.inverse_func is None) or (
                self.func is None and self.inverse_func is not None
            ):
                lacking_param, existing_param = (
                    ("func", "inverse_func")
                    if self.func is None
                    else ("inverse_func", "func")
                )
                raise ValueError(
                    f"When '{existing_param}' is provided, '{lacking_param}' must also"
                    f" be provided. If {lacking_param} is supposed to be the default,"
                    " you need to explicitly pass it the identity function."
                )
            self.transformer_ = FunctionTransformer(
                func=self.func,
                inverse_func=self.inverse_func,
                validate=True,
                check_inverse=self.check_inverse,
            )
            # We are transforming the target here and not the features, so we set the
            # output of FunctionTransformer() to be a numpy array (default) and to not
            # depend on the global configuration:
            self.transformer_.set_output(transform="default")
        # XXX: sample_weight is not currently passed to the
        # transformer. However, if transformer starts using sample_weight, the
        # code should be modified accordingly. At the time to consider the
        # sample_prop feature, it is also a good use case to be considered.
        self.transformer_.fit(y)
        if self.check_inverse:
            idx_selected = slice(None, None, max(1, y.shape[0] // 10))
            y_sel = _safe_indexing(y, idx_selected)
            y_sel_t = self.transformer_.transform(y_sel)
            if not np.allclose(y_sel, self.transformer_.inverse_transform(y_sel_t)):
                warnings.warn(
                    (
                        "The provided functions or transformer are"
                        " not strictly inverse of each other. If"
                        " you are sure you want to proceed regardless"
                        ", set 'check_inverse=False'"
                    ),
                    UserWarning,
                )