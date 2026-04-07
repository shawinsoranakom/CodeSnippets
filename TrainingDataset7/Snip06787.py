def _handle_param(self, value, param_name="", check_types=None):
        if not hasattr(value, "resolve_expression"):
            if check_types and not isinstance(value, check_types):
                raise TypeError(
                    "The %s parameter has the wrong type: should be %s."
                    % (param_name, check_types)
                )
        return value