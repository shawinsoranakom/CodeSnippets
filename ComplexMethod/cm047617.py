def _optimize_type_datetime(condition, model):
    """Make sure we have a datetime type in the value"""
    field_expr = condition.field_expr
    operator = condition.operator
    if (
        operator not in ('in', 'not in', '>', '<', '<=', '>=')
        or "." in field_expr
    ):
        return condition
    value, is_date = _value_to_datetime(condition.value, model.env, iso_only=True)

    # Handle inequality
    if operator[0] in ('<', '>'):
        if value is False:
            return _FALSE_DOMAIN
        if not isinstance(value, datetime):
            return condition
        if value.microsecond:
            assert not is_date, "date don't have microseconds"
            value = value.replace(microsecond=0)
        delta = timedelta(days=1) if is_date else timedelta(seconds=1)
        if operator == '>':
            try:
                value += delta
            except OverflowError:
                # higher than max, not possible
                return _FALSE_DOMAIN
            operator = '>='
        elif operator == '<=':
            try:
                value += delta
            except OverflowError:
                # lower than max, just check if field is set
                return DomainCondition(field_expr, '!=', False)
            operator = '<'

    # Handle equality: compare to the whole second
    if (
        operator in ('in', 'not in')
        and isinstance(value, COLLECTION_TYPES)
        and any(isinstance(v, datetime) for v in value)
    ):
        delta = timedelta(seconds=1)
        domain = DomainOr.apply(
            DomainCondition(field_expr, '>=', v.replace(microsecond=0))
            & DomainCondition(field_expr, '<', v.replace(microsecond=0) + delta)
            if isinstance(v, datetime) else DomainCondition(field_expr, '=', v)
            for v in value
        )
        if operator == 'not in':
            domain = ~domain
        return domain

    return DomainCondition(field_expr, operator, value)