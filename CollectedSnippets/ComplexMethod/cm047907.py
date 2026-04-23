def _search_analytic_distribution(self, operator, value):
        # Don't use this override when account_report_analytic_groupby is truly in the context
        # Indeed, when account_report_analytic_groupby is in the context it means that `analytic_distribution`
        # doesn't have the same format and the table is a temporary one, see _prepare_lines_for_analytic_groupby
        if self.env.context.get('account_report_analytic_groupby') or (operator in ('in', 'not in') and False in value):
            return Domain('analytic_distribution', operator, value)

        def search_value(value: str, exact: bool):
            return list(self.env['account.analytic.account']._search(
                [('display_name', ('=' if exact else 'ilike'), value)]
            ))

        # reformulate the condition as <field> in/not in <ids>
        if operator in ('in', 'not in'):
            ids = [
                r
                for v in value
                for r in (search_value(v, exact=True) if isinstance(value, str) else [v])
            ]
        elif operator in ('ilike', 'not ilike'):
            ids = search_value(value, exact=False)
            operator = 'not in' if operator.startswith('not') else 'in'
        else:
            raise UserError(_('Operation not supported'))

        if not ids:
            # not ids found, just let it optimize to a constant
            return Domain(operator == 'not in')

        # keys can be comma-separated ids, we will split those into an array and then make an array comparison with the list of ids to check
        ids = [str(id_) for id_ in ids if id_]  # list of ids -> list of string
        if operator == 'in':
            return Domain.custom(to_sql=lambda model, alias, query: SQL(
                "%s && %s",
                self._query_analytic_accounts(alias),
                ids,
            ))
        else:
            return Domain.custom(to_sql=lambda model, alias, query: SQL(
                "(NOT %s && %s OR %s IS NULL)",
                self._query_analytic_accounts(alias),
                ids,
                model._field_to_sql(alias, 'analytic_distribution', query),
            ))