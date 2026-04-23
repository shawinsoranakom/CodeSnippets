def check_expression_support(self, expression):
        if isinstance(expression, UNSUPPORTED_DATETIME_AGGREGATES):
            for expr in expression.get_source_expressions():
                try:
                    output_field = expr.output_field
                except (AttributeError, FieldError):
                    # Not every subexpression has an output_field which is fine
                    # to ignore.
                    pass
                else:
                    if isinstance(output_field, DATETIME_FIELDS):
                        klass = expression.__class__.__name__
                        raise NotSupportedError(
                            f"SQLite does not support {klass} on date or time "
                            "fields, because they are stored as text."
                        )
        if (
            isinstance(expression, models.Aggregate)
            and expression.distinct
            and len(expression.source_expressions) > 1
        ):
            raise NotSupportedError(
                "SQLite doesn't support DISTINCT on aggregate functions "
                "accepting multiple arguments."
            )