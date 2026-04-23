def resolve_expression(
        self, query=None, allow_joins=True, reuse=None, summarize=False, for_save=False
    ):
        resolved = super().resolve_expression(
            query,
            allow_joins,
            reuse,
            summarize,
            for_save,
        )
        if not isinstance(self, (DurationExpression, TemporalSubtraction)):
            try:
                lhs_type = resolved.lhs.output_field.get_internal_type()
            except (AttributeError, FieldError):
                lhs_type = None
            try:
                rhs_type = resolved.rhs.output_field.get_internal_type()
            except (AttributeError, FieldError):
                rhs_type = None
            if "DurationField" in {lhs_type, rhs_type} and lhs_type != rhs_type:
                return DurationExpression(
                    resolved.lhs, resolved.connector, resolved.rhs
                )
            datetime_fields = {"DateField", "DateTimeField", "TimeField"}
            if (
                self.connector == self.SUB
                and lhs_type in datetime_fields
                and lhs_type == rhs_type
            ):
                return TemporalSubtraction(resolved.lhs, resolved.rhs)
        return resolved