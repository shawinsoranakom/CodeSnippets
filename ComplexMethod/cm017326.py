def __init__(self, condition=None, then=None, **lookups):
        if lookups:
            if invalid_kwargs := PROHIBITED_FILTER_KWARGS.intersection(lookups):
                invalid_str = ", ".join(f"'{k}'" for k in sorted(invalid_kwargs))
                raise TypeError(f"The following kwargs are invalid: {invalid_str}")
            if condition is None:
                condition, lookups = Q(**lookups), None
            elif getattr(condition, "conditional", False):
                condition, lookups = Q(condition, **lookups), None
        if condition is None or not getattr(condition, "conditional", False) or lookups:
            raise TypeError(
                "When() supports a Q object, a boolean expression, or lookups "
                "as a condition."
            )
        if isinstance(condition, Q) and not condition:
            raise ValueError("An empty Q() can't be used as a When() condition.")
        super().__init__(output_field=None)
        self.condition = condition
        self.result = self._parse_expressions(then)[0]