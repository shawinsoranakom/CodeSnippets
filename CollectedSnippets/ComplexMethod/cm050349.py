def _domain_asks_for_industries(domain):
    for condition in Domain(domain).iter_conditions():
        if condition.field_expr == 'module_type':
            if condition.operator == '=':
                if condition.value == 'industries':
                    return True
            elif condition.operator == 'in' and len(condition.value) == 1:
                if 'industries' in condition.value:
                    return True
            else:
                raise UserError(f'Unsupported domain condition {condition!r}')  # pylint: disable=missing-gettext
    return False