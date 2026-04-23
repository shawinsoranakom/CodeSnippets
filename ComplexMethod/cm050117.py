def generic_search_display_name(self, operator, value):
    if operator != 'in':
        return NotImplemented
    ids = [
        int(id_str)
        for v in value
        if isinstance(v, str)
        and (parts := v.split(':'))
        and len(parts) == 2
        and parts[0] == self._name
        and (id_str := parts[1]).isdigit()
    ]
    return [('value', 'in', ids)]