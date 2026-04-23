def _search_address_search(self, operator, value):
        def make_codomain(value):
            return Domain.OR(
                Domain(field, 'ilike', value)
                for field in ('name', 'street', 'street2', 'city', 'zip', 'state_id', 'country_id')
            )
        if isinstance(value, Domain):
            domain = value.map_conditions(lambda cond: cond if cond.field_expr != 'display_name' else make_codomain(cond.value))
            return Domain('address_id', operator, domain)
        if operator == 'ilike' and isinstance(value, str):
            return Domain('address_id', 'any', make_codomain(value))
        # for the trivial "empty" case, there is no empty address
        if operator == 'in' and (not value or not any(value)):
            return Domain(False)
        return NotImplemented