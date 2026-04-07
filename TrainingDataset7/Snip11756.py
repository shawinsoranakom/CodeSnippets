def __init__(
        self,
        *expressions,
        fields=(),
        name=None,
        db_tablespace=None,
        opclasses=(),
        condition=None,
        include=None,
    ):
        if opclasses and not name:
            raise ValueError("An index must be named to use opclasses.")
        if not isinstance(condition, (NoneType, Q)):
            raise ValueError("Index.condition must be a Q instance.")
        if condition and not name:
            raise ValueError("An index must be named to use condition.")
        if not isinstance(fields, (list, tuple)):
            raise ValueError("Index.fields must be a list or tuple.")
        if not isinstance(opclasses, (list, tuple)):
            raise ValueError("Index.opclasses must be a list or tuple.")
        if not expressions and not fields:
            raise ValueError(
                "At least one field or expression is required to define an index."
            )
        if expressions and fields:
            raise ValueError(
                "Index.fields and expressions are mutually exclusive.",
            )
        if expressions and not name:
            raise ValueError("An index must be named to use expressions.")
        if expressions and opclasses:
            raise ValueError(
                "Index.opclasses cannot be used with expressions. Use "
                "django.contrib.postgres.indexes.OpClass() instead."
            )
        if opclasses and len(fields) != len(opclasses):
            raise ValueError(
                "Index.fields and Index.opclasses must have the same number of "
                "elements."
            )
        if fields and not all(isinstance(field, str) for field in fields):
            raise ValueError("Index.fields must contain only strings with field names.")
        if include and not name:
            raise ValueError("A covering index must be named.")
        if not isinstance(include, (NoneType, list, tuple)):
            raise ValueError("Index.include must be a list or tuple.")
        self.fields = list(fields)
        # A list of 2-tuple with the field name and ordering ('' or 'DESC').
        self.fields_orders = [
            (field_name.removeprefix("-"), "DESC" if field_name.startswith("-") else "")
            for field_name in self.fields
        ]
        self.name = name or ""
        self.db_tablespace = db_tablespace
        self.opclasses = opclasses
        self.condition = condition
        self.include = tuple(include) if include else ()
        self.expressions = tuple(
            F(expression) if isinstance(expression, str) else expression
            for expression in expressions
        )