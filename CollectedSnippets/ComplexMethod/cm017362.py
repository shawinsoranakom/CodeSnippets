def __init__(
        self,
        *expressions,
        fields=(),
        name,
        condition=None,
        deferrable=None,
        include=None,
        opclasses=(),
        nulls_distinct=None,
        violation_error_code=None,
        violation_error_message=None,
    ):
        if not name:
            raise ValueError("A unique constraint must be named.")
        if not expressions and not fields:
            raise ValueError(
                "At least one field or expression is required to define a "
                "unique constraint."
            )
        if expressions and fields:
            raise ValueError(
                "UniqueConstraint.fields and expressions are mutually exclusive."
            )
        if not isinstance(condition, (NoneType, Q)):
            raise ValueError("UniqueConstraint.condition must be a Q instance.")
        if condition and deferrable:
            raise ValueError("UniqueConstraint with conditions cannot be deferred.")
        if include and deferrable:
            raise ValueError("UniqueConstraint with include fields cannot be deferred.")
        if opclasses and deferrable:
            raise ValueError("UniqueConstraint with opclasses cannot be deferred.")
        if expressions and deferrable:
            raise ValueError("UniqueConstraint with expressions cannot be deferred.")
        if expressions and opclasses:
            raise ValueError(
                "UniqueConstraint.opclasses cannot be used with expressions. "
                "Use django.contrib.postgres.indexes.OpClass() instead."
            )
        if not isinstance(deferrable, (NoneType, Deferrable)):
            raise TypeError(
                "UniqueConstraint.deferrable must be a Deferrable instance."
            )
        if not isinstance(include, (NoneType, list, tuple)):
            raise TypeError("UniqueConstraint.include must be a list or tuple.")
        if not isinstance(opclasses, (list, tuple)):
            raise TypeError("UniqueConstraint.opclasses must be a list or tuple.")
        if not isinstance(nulls_distinct, (NoneType, bool)):
            raise TypeError("UniqueConstraint.nulls_distinct must be a bool.")
        if opclasses and len(fields) != len(opclasses):
            raise ValueError(
                "UniqueConstraint.fields and UniqueConstraint.opclasses must "
                "have the same number of elements."
            )
        self.fields = tuple(fields)
        self.condition = condition
        self.deferrable = deferrable
        self.include = tuple(include) if include else ()
        self.opclasses = opclasses
        self.nulls_distinct = nulls_distinct
        self.expressions = tuple(
            F(expression) if isinstance(expression, str) else expression
            for expression in expressions
        )
        super().__init__(
            name=name,
            violation_error_code=violation_error_code,
            violation_error_message=violation_error_message,
        )