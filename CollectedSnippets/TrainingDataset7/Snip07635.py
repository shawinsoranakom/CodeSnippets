def __init_subclass__(cls, /, *args, **kwargs):
        warnings.warn(
            "OrderableAggMixin is deprecated. Use Aggregate and allow_order_by "
            "instead.",
            category=RemovedInDjango70Warning,
            stacklevel=1,
        )
        super().__init_subclass__(*args, **kwargs)