def _search_display_name(self, operator, value):
        # Try to reverse the `display_name` structure
        if operator == 'in':
            return Domain.OR(self._search_display_name('=', v) for v in value)
        if operator == 'not in':
            return NotImplemented
        parts = isinstance(value, str) and value.split(': ')
        if parts and len(parts) == 2:
            return Domain('warehouse_id.name', operator, parts[0]) & Domain('name', operator, parts[1])
        if operator == '=':
            operator = 'in'
            value = [value]
        return super()._search_display_name(operator, value)