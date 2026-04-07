def __init__(
        self,
        *,
        name,
        expressions,
        index_type=None,
        condition=None,
        deferrable=None,
        include=None,
        violation_error_code=None,
        violation_error_message=None,
    ):
        if index_type and index_type.lower() not in {"gist", "hash", "spgist"}:
            raise ValueError(
                "Exclusion constraints only support GiST, Hash, or SP-GiST indexes."
            )
        if not expressions:
            raise ValueError(
                "At least one expression is required to define an exclusion "
                "constraint."
            )
        if not all(
            isinstance(expr, (list, tuple)) and len(expr) == 2 for expr in expressions
        ):
            raise ValueError("The expressions must be a list of 2-tuples.")
        if not isinstance(condition, (NoneType, Q)):
            raise ValueError("ExclusionConstraint.condition must be a Q instance.")
        if not isinstance(deferrable, (NoneType, Deferrable)):
            raise ValueError(
                "ExclusionConstraint.deferrable must be a Deferrable instance."
            )
        if not isinstance(include, (NoneType, list, tuple)):
            raise ValueError("ExclusionConstraint.include must be a list or tuple.")
        if index_type and index_type.lower() == "hash":
            if include:
                raise ValueError(
                    "Covering exclusion constraints using Hash indexes are not "
                    "supported."
                )
            if not expressions:
                pass
            elif len(expressions) > 1:
                raise ValueError(
                    "Composite exclusion constraints using Hash indexes are not "
                    "supported."
                )
            elif expressions[0][1] != RangeOperators.EQUAL:
                raise ValueError(
                    "Exclusion constraints using Hash indexes only support the EQUAL "
                    "operator."
                )
        self.expressions = expressions
        self.index_type = index_type or "GIST"
        self.condition = condition
        self.deferrable = deferrable
        self.include = tuple(include) if include else ()
        super().__init__(
            name=name,
            violation_error_code=violation_error_code,
            violation_error_message=violation_error_message,
        )