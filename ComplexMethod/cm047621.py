def _optimize_m2o_bypass_comodel_id_lookup(condition, model):
    """Avoid comodel's subquery, if it can be compared with the field directly"""
    operator = condition.operator
    if (
        operator in ('any!', 'not any!')
        and isinstance(subdomain := condition.value, DomainCondition)
        and subdomain.field_expr == 'id'
        and (suboperator := subdomain.operator) in ('in', 'not in', 'any!', 'not any!')
    ):
        # We are bypassing permissions, we can transform:
        #  a ANY (id IN X)  =>  a IN (X - {False})
        #  a ANY (id NOT IN X)  =>  a NOT IN (X | {False})
        #  a ANY (id ANY X)  =>  a ANY X
        #  a ANY (id NOT ANY X)  =>  a != False AND a NOT ANY X
        #  a NOT ANY (id IN X)  =>  a NOT IN (X - {False})
        #  a NOT ANY (id NOT IN X)  =>  a IN (X | {False})
        #  a NOT ANY (id ANY X)  =>  a NOT ANY X
        #  a NOT ANY (id NOT ANY X)  =>  a = False OR a ANY X
        val = subdomain.value
        match suboperator:
            case 'in':
                domain = DomainCondition(condition.field_expr, 'in', val - {False})
            case 'not in':
                domain = DomainCondition(condition.field_expr, 'not in', val | {False})
            case 'any!':
                domain = DomainCondition(condition.field_expr, 'any!', val)
            case 'not any!':
                domain = DomainCondition(condition.field_expr, '!=', False) \
                    & DomainCondition(condition.field_expr, 'not any!', val)
        if operator == 'not any!':
            domain = ~domain
        return domain

    return condition