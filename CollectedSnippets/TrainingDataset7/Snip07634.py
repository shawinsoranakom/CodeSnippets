def __init__(self, expression, delimiter, **extra):
        if isinstance(delimiter, str):
            warnings.warn(
                "delimiter: str will be resolved as a field reference instead "
                "of a string literal on Django 7.0. Pass "
                f"`delimiter=Value({delimiter!r})` to preserve the previous behavior.",
                category=RemovedInDjango70Warning,
                stacklevel=2,
            )

            delimiter = Value(delimiter)

        warnings.warn(
            "The PostgreSQL specific StringAgg function is deprecated. Use "
            "django.db.models.aggregates.StringAgg instead.",
            category=RemovedInDjango70Warning,
            stacklevel=2,
        )

        super().__init__(expression, delimiter, **extra)