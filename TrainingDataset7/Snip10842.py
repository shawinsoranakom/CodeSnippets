def as_sql(self, *args, **kwargs):
        raise ValueError(
            "This queryset contains a reference to an outer query and may "
            "only be used in a subquery."
        )