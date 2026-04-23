def resolve_lookup_value(self, value, can_reuse, allow_joins, summarize=False):
        if hasattr(value, "resolve_expression"):
            value = value.resolve_expression(
                self,
                reuse=can_reuse,
                allow_joins=allow_joins,
                summarize=summarize,
            )
        elif isinstance(value, (list, tuple)):
            # The items of the iterable may be expressions and therefore need
            # to be resolved independently.
            values = (
                self.resolve_lookup_value(sub_value, can_reuse, allow_joins, summarize)
                for sub_value in value
            )
            type_ = type(value)
            if hasattr(type_, "_make"):  # namedtuple
                return type_(*values)
            return type_(values)
        return value