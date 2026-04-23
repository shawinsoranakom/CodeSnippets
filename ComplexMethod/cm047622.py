def _merge_set_conditions(cls: type[DomainNary], conditions):
    """Base function to merge equality conditions.

    Combine the 'in' and 'not in' conditions to a single set of values.

    Examples:

        a in {1} or a in {2}  <=>  a in {1, 2}
        a in {1, 2} and a not in {2, 5}  =>  a in {1}
    """
    assert all(isinstance(cond.value, OrderedSet) for cond in conditions)

    # build the sets for 'in' and 'not in' conditions
    in_sets = [c.value for c in conditions if c.operator == 'in']
    not_in_sets = [c.value for c in conditions if c.operator == 'not in']

    # combine the sets
    field_expr = conditions[0].field_expr
    if cls.OPERATOR == '&':
        if in_sets:
            return [DomainCondition(field_expr, 'in', intersection(in_sets) - union(not_in_sets))]
        else:
            return [DomainCondition(field_expr, 'not in', union(not_in_sets))]
    else:
        if not_in_sets:
            return [DomainCondition(field_expr, 'not in', intersection(not_in_sets) - union(in_sets))]
        else:
            return [DomainCondition(field_expr, 'in', union(in_sets))]