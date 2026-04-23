def _optimize_in_set(condition, _model):
    """Make sure the value is an OrderedSet or use 'any' operator"""
    value = condition.value
    if isinstance(value, OrderedSet) and value:
        # very common case, just skip creation of a new Domain instance
        return condition
    if isinstance(value, ANY_TYPES):
        operator = 'any' if condition.operator == 'in' else 'not any'
        return DomainCondition(condition.field_expr, operator, value)
    if not value:
        return _FALSE_DOMAIN if condition.operator == 'in' else _TRUE_DOMAIN
    if not isinstance(value, COLLECTION_TYPES):
        # TODO show warning, note that condition.field_expr in ('group_ids', 'user_ids') gives a lot of them
        _logger.debug("The domain condition %r should have a list value.", condition)
        value = [value]
    return DomainCondition(condition.field_expr, condition.operator, OrderedSet(value))