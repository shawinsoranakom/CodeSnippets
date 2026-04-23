def resolve_expression(
        self, query=None, allow_joins=True, reuse=None, summarize=False, for_save=False
    ):
        copy = super().resolve_expression(
            query, allow_joins, reuse, summarize, for_save
        )
        field = copy.lhs.output_field
        # DateTimeField is a subclass of DateField so this works for both.
        if not isinstance(field, (DateField, TimeField)):
            raise TypeError(
                "%r isn't a DateField, TimeField, or DateTimeField." % field.name
            )
        # If self.output_field was None, then accessing the field will trigger
        # the resolver to assign it to self.lhs.output_field.
        if not isinstance(copy.output_field, (DateField, DateTimeField, TimeField)):
            raise ValueError(
                "output_field must be either DateField, TimeField, or DateTimeField"
            )
        # Passing dates or times to functions expecting datetimes is most
        # likely a mistake.
        class_output_field = (
            self.__class__.output_field
            if isinstance(self.__class__.output_field, Field)
            else None
        )
        output_field = class_output_field or copy.output_field
        has_explicit_output_field = (
            class_output_field or field.__class__ is not copy.output_field.__class__
        )
        if type(field) is DateField and (
            isinstance(output_field, DateTimeField)
            or copy.kind in ("hour", "minute", "second", "time")
        ):
            raise ValueError(
                "Cannot truncate DateField '%s' to %s."
                % (
                    field.name,
                    (
                        output_field.__class__.__name__
                        if has_explicit_output_field
                        else "DateTimeField"
                    ),
                )
            )
        elif isinstance(field, TimeField) and (
            isinstance(output_field, DateTimeField)
            or copy.kind in ("year", "quarter", "month", "week", "day", "date")
        ):
            raise ValueError(
                "Cannot truncate TimeField '%s' to %s."
                % (
                    field.name,
                    (
                        output_field.__class__.__name__
                        if has_explicit_output_field
                        else "DateTimeField"
                    ),
                )
            )
        return copy