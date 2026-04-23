def _optimize_boolean_in(condition, model):
    """b in boolean_values"""
    value = condition.value
    operator = condition.operator
    if operator not in ('in', 'not in') or not isinstance(value, COLLECTION_TYPES):
        condition._raise("Cannot compare %r to %s which is not a collection of length 1", condition.field_expr, type(value))
    if not all(isinstance(v, bool) for v in value):
        # parse the values
        if any(isinstance(v, str) for v in value):
            # TODO make a warning
            _logger.debug("Comparing boolean with a string in %s", condition)
        value = {
            str2bool(v.lower(), False) if isinstance(v, str) else bool(v)
            for v in value
        }
    if len(value) == 1 and not any(value):
        # when comparing boolean values, always compare to [True] if possible
        # it eases the implementation of search methods
        operator = _INVERSE_OPERATOR[operator]
        value = [True]
    return DomainCondition(condition.field_expr, operator, value)