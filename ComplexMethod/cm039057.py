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