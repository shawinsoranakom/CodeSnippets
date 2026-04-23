def __init__(
        self,
        *expressions,
        distinct=False,
        filter=None,
        default=None,
        order_by=None,
        **extra,
    ):
        if distinct and not self.allow_distinct:
            raise TypeError("%s does not allow distinct." % self.__class__.__name__)
        if order_by and not self.allow_order_by:
            raise TypeError("%s does not allow order_by." % self.__class__.__name__)
        if default is not None and self.empty_result_set_value is not None:
            raise TypeError(f"{self.__class__.__name__} does not allow default.")

        self.distinct = distinct
        self.filter = None if filter is None else AggregateFilter(filter)
        self.default = default
        self.order_by = AggregateOrderBy.from_param(
            f"{self.__class__.__name__}.order_by", order_by
        )
        super().__init__(*expressions, **extra)