def __init_subclass__(cls, **kwargs):
        # RemovedInDjango70Warning: When the deprecation ends, remove
        # completely.
        # Allow for both `get_placeholder` and `get_placeholder_sql` to
        # be declared to ease the deprecation process for third-party apps.
        if (
            get_placeholder := cls.__dict__.get("get_placeholder")
        ) is not None and "get_placeholder_sql" not in cls.__dict__:
            warnings.warn(
                "Field.get_placeholder is deprecated in favor of get_placeholder_sql. "
                f"Define {cls.__module__}.{cls.__qualname__}.get_placeholder_sql "
                "to return both SQL and parameters instead.",
                category=RemovedInDjango70Warning,
                skip_file_prefixes=django_file_prefixes(),
            )

            def get_placeholder_sql(self, value, compiler, connection):
                placeholder = get_placeholder(self, value, compiler, connection)
                if hasattr(value, "as_sql"):
                    sql, params = compiler.compile(value)
                    return placeholder % sql, params
                return placeholder, (value,)

            setattr(cls, "get_placeholder_sql", get_placeholder_sql)
        return super().__init_subclass__(**kwargs)