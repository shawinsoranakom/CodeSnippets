def _optimize_nary_sort_key(domain: Domain) -> tuple[str, str, str]:
    """Sorting key for nary domains so that similar operators are grouped together.

    1. Field name (non-simple conditions are sorted at the end)
    2. Operator type (equality, inequality, existence, string comparison, other)
    3. Operator

    Sorting allows to have the same optimized domain for equivalent conditions.
    For debugging, it eases to find conditions on fields.
    The generated SQL will be ordered by field name so that database caching
    can be applied more frequently.
    """
    if isinstance(domain, DomainCondition):
        # group the same field and same operator together
        operator = domain.operator
        positive_op = NEGATIVE_CONDITION_OPERATORS.get(operator, operator)
        if positive_op == 'in':
            order = "0in"
        elif positive_op == 'any':
            order = "1any"
        elif positive_op == 'any!':
            order = "2any"
        elif positive_op.endswith('like'):
            order = "like"
        else:
            order = positive_op
        return domain.field_expr, order, operator
    elif hasattr(domain, 'OPERATOR') and isinstance(domain.OPERATOR, str):
        # in python; '~' > any letter
        return '~', '', domain.OPERATOR
    else:
        return '~', '~', domain.__class__.__name__