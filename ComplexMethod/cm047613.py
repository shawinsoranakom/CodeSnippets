def _optimize_relational_name_search(condition, model):
    """Search relational using `display_name`.

    When a relational field is compared to a string, we actually want to make
    a condition on the `display_name` field.
    Negative conditions are translated into a "not any" for consistency.
    """
    operator = condition.operator
    value = condition.value
    positive_operator = NEGATIVE_CONDITION_OPERATORS.get(operator, operator)
    any_operator = 'any' if positive_operator == operator else 'not any'
    # Handle like operator
    if operator.endswith('like'):
        return DomainCondition(
            condition.field_expr,
            any_operator,
            DomainCondition('display_name', positive_operator, value),
        )
    # Handle inequality as not supported
    if operator[0] in ('<', '>') and isinstance(value, str):
        condition._raise("Inequality not supported for relational field using a string", error=TypeError)
    # Handle equality with str values
    if positive_operator != 'in' or not isinstance(value, COLLECTION_TYPES):
        return condition
    str_values, other_values = partition(lambda v: isinstance(v, str), value)
    if not str_values:
        return condition
    domain = DomainCondition(
        condition.field_expr,
        any_operator,
        DomainCondition('display_name', positive_operator, str_values),
    )
    if other_values:
        if positive_operator == operator:
            domain |= DomainCondition(condition.field_expr, operator, other_values)
        else:
            domain &= DomainCondition(condition.field_expr, operator, other_values)
    return domain