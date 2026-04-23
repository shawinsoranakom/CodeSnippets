def formatted_read_group(self, domain, groupby=(), aggregates=(), having=(), offset=0, limit=None, order=None) -> list[dict]:
        # Add latest running_balance in the formatted_read_group
        result = super().formatted_read_group(
            domain, groupby, aggregates, having=having,
            offset=offset, limit=limit, order=order)
        show_running_balance = False
        # We loop over the content of groupby because the groupby date is in the form of "date:granularity"
        for el in groupby:
            if (el == 'statement_id' or el == 'journal_id' or el.startswith('date')) and self.env.context.get('show_running_balance_latest'):
                show_running_balance = True
                break
        if show_running_balance:
            for group_line in result:
                group_line['running_balance'] = self.search(group_line['__extra_domain'] + domain, limit=1).running_balance or 0.0
        return result