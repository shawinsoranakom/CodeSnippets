def process_rhs(self, compiler, connection):
        if self.rhs is None and not isinstance(self.lhs, KeyTransform):
            warnings.warn(
                "Using None as the right-hand side of an exact lookup on JSONField to "
                "mean JSON scalar 'null' is deprecated. Use JSONNull() instead (or use "
                "the __isnull lookup if you meant SQL NULL).",
                RemovedInDjango70Warning,
                skip_file_prefixes=django_file_prefixes(),
            )

        rhs, rhs_params = super().process_rhs(compiler, connection)

        # RemovedInDjango70Warning: When the deprecation period is over, remove
        # The following if-block entirely.
        # Treat None lookup values as null.
        if rhs == "%s" and (*rhs_params,) == (None,):
            rhs_params = ("null",)
        if connection.vendor == "mysql" and not isinstance(
            self.rhs, expressions.JSONNull
        ):
            func = ["JSON_EXTRACT(%s, '$')"] * len(rhs_params)
            rhs %= tuple(func)
        return rhs, rhs_params