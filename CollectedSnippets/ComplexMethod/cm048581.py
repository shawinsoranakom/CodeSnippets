def _get_bank_cash_graph_data(self):
        """Computes the data used to display the graph for bank and cash journals in the accounting dashboard"""
        def build_graph_data(date, amount, currency):
            #display date in locale format
            name = format_date(date, 'd LLLL Y', locale=locale)
            short_name = format_date(date, 'd MMM', locale=locale)
            return {'x': short_name, 'y': currency.round(amount), 'name': name}

        today = datetime.today()
        last_month = today + timedelta(days=-30)
        locale = get_lang(self.env).code

        query = """
            SELECT move.journal_id,
                   move.date,
                   SUM(st_line.amount) AS amount
              FROM account_bank_statement_line st_line
              JOIN account_move move ON move.id = st_line.move_id
             WHERE move.journal_id = ANY(%s)
               AND move.date > %s
               AND move.company_id = ANY(%s)
          GROUP BY move.date, move.journal_id
          ORDER BY move.date DESC
        """
        self.env.cr.execute(query, (self.ids, last_month, self.env.companies.ids))
        query_result = group_by_journal(self.env.cr.dictfetchall())

        result = {}
        for journal in self:
            graph_title, graph_key = journal._graph_title_and_key()
            # User may have read access on the journal but not on the company
            currency = journal.currency_id or self.env['res.currency'].browse(journal.company_id.sudo().currency_id.id)
            journal_result = query_result[journal.id]

            color = '#875A7B' if 'e' in version else '#7c7bad'
            is_sample_data = not journal_result and not journal.has_statement_lines

            data = []
            if is_sample_data:
                for i in range(30, 0, -5):
                    current_date = today + timedelta(days=-i)
                    data.append(build_graph_data(current_date, random.randint(-5, 15), currency))
                    graph_key = _('Sample data')
            else:
                last_balance = journal.current_statement_balance
                # Make sure the last point in the graph is at least today or a future date
                if not journal_result or journal_result[0]['date'] < today.date():
                    data.append(build_graph_data(today, last_balance, currency))
                date = today
                amount = last_balance
                #then we subtract the total amount of bank statement lines per day to get the previous points
                #(graph is drawn backward)
                for val in journal_result:
                    date = val['date']
                    data[:0] = [build_graph_data(date, amount, currency)]
                    amount -= val['amount']

                # make sure the graph starts 1 month ago
                if date.strftime(DF) != last_month.strftime(DF):
                    data[:0] = [build_graph_data(last_month, amount, currency)]

            result[journal.id] = [{'values': data, 'title': graph_title, 'key': graph_key, 'area': True, 'color': color, 'is_sample_data': is_sample_data}]
        return result