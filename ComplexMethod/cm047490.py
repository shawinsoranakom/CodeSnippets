def filter_function(self, records, field_expr, operator, value):
        getter = self.expression_getter(field_expr)

        if (self.bypass_search_access or operator == 'any!') and not records.env.su:
            # When filtering with bypass access, search the corecords with sudo
            # and a special key in the context. To evaluate sub-domains, the
            # special key makes the environment un-sudoed before evaluation.
            expr_getter = getter
            sudo_env = records.sudo().with_context(filter_function_reset_sudo=True).env
            getter = lambda rec: expr_getter(rec.with_env(sudo_env))  # noqa: E731

        corecords = getter(records)
        if operator in ('any', 'any!'):
            assert isinstance(value, Domain)
            if operator == 'any' and records.env.context.get('filter_function_reset_sudo'):
                corecords = corecords.sudo(False)._filtered_access('read')
            corecords = corecords.filtered_domain(value)
        elif operator == 'in' and isinstance(value, COLLECTION_TYPES):
            value = set(value)
            if False in value:
                if not corecords:
                    # shortcut, we know none of records has a corecord
                    return lambda _: True
                if len(value) > 1:
                    value.discard(False)
                    filter_values = self.filter_function(records, field_expr, 'in', value)
                    return lambda rec: not getter(rec) or filter_values(rec)
                return lambda rec: not getter(rec)
            corecords = corecords.filtered_domain(Domain('id', 'in', value))
        else:
            corecords = corecords.filtered_domain(Domain('id', operator, value))

        if not corecords:
            return lambda _: False

        ids = set(corecords._ids)
        return lambda rec: any(id_ in ids for val in getter(rec) for id_ in val._ids)