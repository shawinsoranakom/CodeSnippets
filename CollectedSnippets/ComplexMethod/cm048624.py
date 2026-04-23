def _search_account_root(self, operator, value):
        if operator not in ('in', 'child_of', 'any'):
            return NotImplemented
        if operator == 'any':
            if isinstance(value, Domain) and value.field_expr == 'display_name' and value.operator == 'in':
                roots = self.env['account.root'].browse(value.value)
            else:
                return NotImplemented
        else:
            roots = self.env['account.root'].browse(value)
        return Domain.OR(
            Domain('placeholder_code', '=ilike', root.name + ('' if operator in ['in', 'any'] and not root.parent_id else '%'))
            for root in roots
        )