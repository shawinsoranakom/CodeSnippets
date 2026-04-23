def _search_complete_name(self, operator, value):
        supported_operators = ["=", "!=", "ilike", "not ilike", "in", "not in", "=ilike"]
        if operator not in supported_operators or not isinstance(value, (str, list)):
            raise NotImplementedError(_('Operation not Supported.'))
        department = self.env['hr.department'].search([])
        if operator == '=':
            department = department.filtered(lambda m: m.complete_name == value)
        elif operator == '!=':
            department = department.filtered(lambda m: m.complete_name != value)
        elif operator == 'ilike':
            department = department.filtered(lambda m: value.lower() in m.complete_name.lower())
        elif operator == 'not ilike':
            department = department.filtered(lambda m: value.lower() not in m.complete_name.lower())
        elif operator == 'in':
            department = department.filtered(lambda m: m.complete_name in value)
        elif operator == 'not in':
            department = department.filtered(lambda m: m.complete_name not in value)
        elif operator == '=ilike':
            pattern = re.compile(re.escape(value).replace('%', '.*').replace('_', '.'), flags=re.IGNORECASE)
            department = department.filtered(lambda m: pattern.fullmatch(m.complete_name))
        return [('id', 'in', department.ids)]