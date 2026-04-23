def _get_params_html(self, deep=True, doc_link=""):
        """
        Get parameters for this estimator with a specific HTML representation.

        Parameters
        ----------
        deep : bool, default=True
            If True, will return the parameters for this estimator and
            contained subobjects that are estimators.

        doc_link : str
            URL to the estimator documentation.
            Used for linking to the estimator's parameters documentation
            available in HTML displays.

        Returns
        -------
        params : ParamsDict
            Parameter names mapped to their values. We return a `ParamsDict`
            dictionary, which renders a specific HTML representation in table
            form.
        """
        out = self.get_params(deep=deep)

        init_default_params = inspect.signature(self.__init__).parameters
        init_default_params = {
            name: param.default for name, param in init_default_params.items()
        }

        def is_non_default(param_name, param_value):
            """Finds the parameters that have been set by the user."""
            if param_name not in init_default_params:
                # happens if k is part of a **kwargs
                return True
            if init_default_params[param_name] == inspect._empty:
                # k has no default value
                return True
            # avoid calling repr on nested estimators
            if isinstance(param_value, BaseEstimator) and type(param_value) is not type(
                init_default_params[param_name]
            ):
                return True
            if is_pandas_na(param_value) and not is_pandas_na(
                init_default_params[param_name]
            ):
                return True
            if not np.array_equal(
                param_value, init_default_params[param_name]
            ) and not (
                is_scalar_nan(init_default_params[param_name])
                and is_scalar_nan(param_value)
            ):
                return True

            return False

        # Sort parameters so non-default parameters are shown first
        unordered_params = {
            name: out[name] for name in init_default_params if name in out
        }
        unordered_params.update(
            {
                name: value
                for name, value in out.items()
                if name not in init_default_params
            }
        )

        non_default_params, default_params = [], []
        for name, value in unordered_params.items():
            if is_non_default(name, value):
                non_default_params.append(name)
            else:
                default_params.append(name)

        params = {name: out[name] for name in non_default_params + default_params}

        return ParamsDict(
            params=params,
            non_default=tuple(non_default_params),
            estimator_class=self.__class__,
            doc_link=doc_link,
        )