def fix_filter_directive(
    filter: FilterDirective | None,  # noqa: A002
    *,
    allowed_comparators: Sequence[Comparator] | None = None,
    allowed_operators: Sequence[Operator] | None = None,
    allowed_attributes: Sequence[str] | None = None,
) -> FilterDirective | None:
    """Fix invalid filter directive.

    Args:
        filter: Filter directive to fix.
        allowed_comparators: allowed comparators. Defaults to all comparators.
        allowed_operators: allowed operators. Defaults to all operators.
        allowed_attributes: allowed attributes. Defaults to all attributes.

    Returns:
        Fixed filter directive.
    """
    if (
        not (allowed_comparators or allowed_operators or allowed_attributes)
    ) or not filter:
        return filter

    if isinstance(filter, Comparison):
        if allowed_comparators and filter.comparator not in allowed_comparators:
            return None
        if allowed_attributes and filter.attribute not in allowed_attributes:
            return None
        return filter
    if isinstance(filter, Operation):
        if allowed_operators and filter.operator not in allowed_operators:
            return None
        args = [
            cast(
                "FilterDirective",
                fix_filter_directive(
                    arg,
                    allowed_comparators=allowed_comparators,
                    allowed_operators=allowed_operators,
                    allowed_attributes=allowed_attributes,
                ),
            )
            for arg in filter.arguments
            if arg is not None
        ]
        if not args:
            return None
        if len(args) == 1 and filter.operator in (Operator.AND, Operator.OR):
            return args[0]
        return Operation(
            operator=filter.operator,
            arguments=args,
        )
    return filter