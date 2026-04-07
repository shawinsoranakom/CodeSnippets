def resolve_expression(
        self, query=None, allow_joins=True, reuse=None, summarize=False, for_save=False
    ):
        copy = super().resolve_expression(
            query, allow_joins, reuse, summarize, for_save
        )
        field = getattr(copy.lhs, "output_field", None)
        if field is None:
            return copy
        if not isinstance(field, (DateField, DateTimeField, TimeField, DurationField)):
            raise ValueError(
                "Extract input expression must be DateField, DateTimeField, "
                "TimeField, or DurationField."
            )
        # Passing dates to functions expecting datetimes is most likely a
        # mistake.
        if type(field) is DateField and copy.lookup_name in (
            "hour",
            "minute",
            "second",
        ):
            raise ValueError(
                "Cannot extract time component '%s' from DateField '%s'."
                % (copy.lookup_name, field.name)
            )
        if isinstance(field, DurationField) and copy.lookup_name in (
            "year",
            "iso_year",
            "month",
            "week",
            "week_day",
            "iso_week_day",
            "quarter",
        ):
            raise ValueError(
                "Cannot extract component '%s' from DurationField '%s'."
                % (copy.lookup_name, field.name)
            )
        return copy