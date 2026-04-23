def _validate_values_are_expressions(values, method_name):
        invalid_args = sorted(
            str(arg) for arg in values if not hasattr(arg, "resolve_expression")
        )
        if invalid_args:
            raise TypeError(
                "QuerySet.%s() received non-expression(s): %s."
                % (
                    method_name,
                    ", ".join(invalid_args),
                )
            )