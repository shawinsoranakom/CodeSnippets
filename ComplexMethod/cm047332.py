def name_search(self, name='', domain=None, operator='ilike', limit=100):
        result = []
        domain = Domain(domain or Domain.TRUE)
        # first search by code
        if not operator in Domain.NEGATIVE_OPERATORS and name and len(name) == 2:
            countries = self.search_fetch(domain & Domain('code', operator, name), ['display_name'], limit=limit)
            result.extend((country.id, country.display_name) for country in countries.sudo())
            domain &= Domain('id', 'not in', countries.ids)
            if limit is not None:
                limit -= len(countries)
                if limit <= 0:
                    return result
        # normal search
        result.extend(super().name_search(name, domain, operator, limit))
        return result