def __init__(self, lookup, querysets, to_attr=None):
        for queryset in querysets:
            if queryset is not None and (
                isinstance(queryset, RawQuerySet)
                or (
                    hasattr(queryset, "_iterable_class")
                    and not issubclass(queryset._iterable_class, ModelIterable)
                )
            ):
                raise ValueError(
                    "Prefetch querysets cannot use raw(), values(), and values_list()."
                )
        self.querysets = querysets
        super().__init__(lookup, to_attr=to_attr)