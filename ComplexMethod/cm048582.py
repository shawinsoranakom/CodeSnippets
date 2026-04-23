def _get_sale_purchase_graph_data(self):
        today = fields.Date.today()
        day_of_week = int(format_datetime(today, 'e', locale=get_lang(self.env).code))
        first_day_of_week = today + timedelta(days=-day_of_week+1)
        format_month = lambda d: format_date(d, 'MMM', locale=get_lang(self.env).code)

        self.env.cr.execute("""
            SELECT move.journal_id,
                   COALESCE(SUM(move.amount_residual_signed) FILTER (WHERE invoice_date_due < %(start_week1)s), 0) AS total_before,
                   COALESCE(SUM(move.amount_residual_signed) FILTER (WHERE invoice_date_due >= %(start_week1)s AND invoice_date_due < %(start_week2)s), 0) AS total_week1,
                   COALESCE(SUM(move.amount_residual_signed) FILTER (WHERE invoice_date_due >= %(start_week2)s AND invoice_date_due < %(start_week3)s), 0) AS total_week2,
                   COALESCE(SUM(move.amount_residual_signed) FILTER (WHERE invoice_date_due >= %(start_week3)s AND invoice_date_due < %(start_week4)s), 0) AS total_week3,
                   COALESCE(SUM(move.amount_residual_signed) FILTER (WHERE invoice_date_due >= %(start_week4)s AND invoice_date_due < %(start_week5)s), 0) AS total_week4,
                   COALESCE(SUM(move.amount_residual_signed) FILTER (WHERE invoice_date_due >= %(start_week5)s), 0) AS total_after
              FROM account_move move
             WHERE move.journal_id = ANY(%(journal_ids)s)
               AND move.state = 'posted'
               AND move.payment_state in ('not_paid', 'partial')
               AND move.move_type IN %(invoice_types)s
               AND move.company_id = ANY(%(company_ids)s)
          GROUP BY move.journal_id
        """, {
            'invoice_types': tuple(self.env['account.move'].get_invoice_types(True)),
            'journal_ids': self.ids,
            'company_ids': self.env.companies.ids,
            'start_week1': first_day_of_week + timedelta(days=-7),
            'start_week2': first_day_of_week + timedelta(days=0),
            'start_week3': first_day_of_week + timedelta(days=7),
            'start_week4': first_day_of_week + timedelta(days=14),
            'start_week5': first_day_of_week + timedelta(days=21),
        })
        query_results = {r['journal_id']: r for r in self.env.cr.dictfetchall()}
        result = {}
        for journal in self:
            # User may have read access on the journal but not on the company
            currency = journal.currency_id or self.env['res.currency'].browse(journal.company_id.sudo().currency_id.id)
            graph_title, graph_key = journal._graph_title_and_key()
            sign = 1 if journal.type == 'sale' else -1
            journal_data = query_results.get(journal.id)
            data = []
            data.append({'label': _('Due'), 'type': 'past'})
            for i in range(-1, 3):
                if i == 0:
                    label = _('This Week')
                else:
                    start_week = first_day_of_week + timedelta(days=i*7)
                    end_week = start_week + timedelta(days=6)
                    if start_week.month == end_week.month:
                        label = f"{start_week.day} - {end_week.day} {format_month(end_week)}"
                    else:
                        label = f"{start_week.day} {format_month(start_week)} - {end_week.day} {format_month(end_week)}"
                data.append({'label': label, 'type': 'past' if i < 0 else 'future'})
            data.append({'label': _('Not Due'), 'type': 'future'})

            is_sample_data = not journal_data
            if not is_sample_data:
                data[0]['value'] = currency.round(sign * journal_data['total_before'])
                data[1]['value'] = currency.round(sign * journal_data['total_week1'])
                data[2]['value'] = currency.round(sign * journal_data['total_week2'])
                data[3]['value'] = currency.round(sign * journal_data['total_week3'])
                data[4]['value'] = currency.round(sign * journal_data['total_week4'])
                data[5]['value'] = currency.round(sign * journal_data['total_after'])
            else:
                for index in range(6):
                    data[index]['type'] = 'o_sample_data'
                    # we use unrealistic values for the sample data
                    data[index]['value'] = random.randint(0, 20)
                    graph_key = _('Sample data')

            result[journal.id] = [{'values': data, 'title': graph_title, 'key': graph_key, 'is_sample_data': is_sample_data}]
        return result