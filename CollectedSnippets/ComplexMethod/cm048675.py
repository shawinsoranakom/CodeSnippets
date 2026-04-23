def _get_all_reconciled_invoice_partials(self):
        self.ensure_one()
        reconciled_lines = self.line_ids.filtered(lambda line: line.account_id.account_type in ('asset_receivable', 'liability_payable'))
        if not reconciled_lines.ids:
            return {}

        self.env['account.partial.reconcile'].flush_model([
            'credit_amount_currency', 'credit_move_id', 'debit_amount_currency',
            'debit_move_id', 'exchange_move_id',
        ])
        sql = SQL('''
            SELECT
                part.id,
                part.exchange_move_id,
                part.debit_amount_currency AS amount,
                part.credit_move_id AS counterpart_line_id
            FROM account_partial_reconcile part
            WHERE part.debit_move_id IN %(line_ids)s

            UNION ALL

            SELECT
                part.id,
                part.exchange_move_id,
                part.credit_amount_currency AS amount,
                part.debit_move_id AS counterpart_line_id
            FROM account_partial_reconcile part
            WHERE part.credit_move_id IN %(line_ids)s
        ''', line_ids=tuple(reconciled_lines.ids))

        partial_values_list = []
        counterpart_line_ids = set()
        exchange_move_ids = set()
        for values in self.env.execute_query_dict(sql):
            partial_values_list.append({
                'aml_id': values['counterpart_line_id'],
                'partial_id': values['id'],
                'amount': values['amount'],
                'currency': self.currency_id,
            })
            counterpart_line_ids.add(values['counterpart_line_id'])
            if values['exchange_move_id']:
                exchange_move_ids.add(values['exchange_move_id'])

        if exchange_move_ids:
            self.env['account.move.line'].flush_model(['move_id'])
            sql = SQL('''
                SELECT
                    part.id,
                    part.credit_move_id AS counterpart_line_id
                FROM account_partial_reconcile part
                JOIN account_move_line credit_line ON credit_line.id = part.credit_move_id
                WHERE credit_line.move_id IN %(exchange_move_ids)s AND part.debit_move_id IN %(counterpart_line_ids)s

                UNION ALL

                SELECT
                    part.id,
                    part.debit_move_id AS counterpart_line_id
                FROM account_partial_reconcile part
                JOIN account_move_line debit_line ON debit_line.id = part.debit_move_id
                WHERE debit_line.move_id IN %(exchange_move_ids)s AND part.credit_move_id IN %(counterpart_line_ids)s
            ''', exchange_move_ids=tuple(exchange_move_ids), counterpart_line_ids=tuple(counterpart_line_ids))

            for part_id, line_ids in self.env.execute_query(sql):
                counterpart_line_ids.add(line_ids)
                partial_values_list.append({
                    'aml_id': line_ids,
                    'partial_id': part_id,
                    'currency': self.company_id.currency_id,
                })

        counterpart_lines = {x.id: x for x in self.env['account.move.line'].browse(counterpart_line_ids)}
        for partial_values in partial_values_list:
            partial_values['aml'] = counterpart_lines[partial_values['aml_id']]
            partial_values['is_exchange'] = partial_values['aml'].move_id.id in exchange_move_ids
            if partial_values['is_exchange']:
                partial_values['amount'] = abs(partial_values['aml'].balance)

        return partial_values_list