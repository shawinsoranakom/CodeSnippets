def name_search(self, name='', domain=None, operator='ilike', limit=100):
        result = []
        domain = Domain(domain or Domain.TRUE)
        # accepting 'in' as operator (see odoo/addons/base/tests/test_res_country.py)
        if operator == 'in':
            if limit is None:
                limit = 100  # force a limit
            for item in name:
                result.extend(self.name_search(item, domain, operator='=', limit=limit - len(result)))
                if len(result) == limit:
                    break
            return result
        # first search by code (with =ilike)
        if not operator in Domain.NEGATIVE_OPERATORS and name:
            states = self.search_fetch(domain & Domain('code', '=like', name), ['display_name'], limit=limit)
            result.extend((state.id, state.display_name) for state in states.sudo())
            domain &= Domain('id', 'not in', states.ids)
            if limit is not None:
                limit -= len(states)
                if limit <= 0:
                    return result
        # normal search
        result.extend(super().name_search(name, domain, operator, limit))
        return result