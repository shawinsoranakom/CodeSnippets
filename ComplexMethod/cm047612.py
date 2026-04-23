def _optimize_like_str(condition, model):
    """Validate value for pattern matching, must be a str"""
    value = condition.value
    if not value:
        # =like matches only empty string (inverse the condition)
        result = (condition.operator in NEGATIVE_CONDITION_OPERATORS) == ('=' in condition.operator)
        # relational and non-relation fields behave differently
        if condition._field(model).relational or '=' in condition.operator:
            return DomainCondition(condition.field_expr, '!=' if result else '=', False)
        return Domain(result)
    if isinstance(value, str):
        return condition
    if isinstance(value, SQL):
        warnings.warn("Since 19.0, use Domain.custom(to_sql=lambda model, alias, query: SQL(...))", DeprecationWarning)
        return condition
    if '=' in condition.operator:
        condition._raise("The pattern to match must be a string", error=TypeError)
    return DomainCondition(condition.field_expr, condition.operator, str(value))