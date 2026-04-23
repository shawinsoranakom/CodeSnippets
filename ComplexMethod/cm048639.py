def _compute_payment_state(self):
        def _invoice_qualifies(move):
            currency = move.currency_id or move.company_id.currency_id or self.env.company.currency_id
            return move.is_invoice(True) and (
                move.state == 'posted'
                or (move.state == 'draft' and not currency.is_zero(move.amount_total))
            )

        groups = self.grouped(lambda move:
            'legacy' if move.payment_state == 'invoicing_legacy' else
            'blocked' if move.payment_state == 'blocked' else
            'invoices' if _invoice_qualifies(move) else
            'unpaid'
        )
        groups.get('unpaid', self.browse()).payment_state = 'not_paid'
        invoices = groups.get('invoices', self.browse())

        stored_ids = tuple(invoices.ids)
        if stored_ids:
            self.env['account.partial.reconcile'].flush_model()
            self.env['account.payment'].flush_model(['is_matched'])

            queries = []
            for source_field, counterpart_field in (
                ('debit_move_id', 'credit_move_id'),
                ('credit_move_id', 'debit_move_id'),
            ):
                queries.append(SQL('''
                    SELECT
                        source_line.id AS source_line_id,
                        source_line.move_id AS source_move_id,
                        account.account_type AS source_line_account_type,
                        ARRAY_AGG(counterpart_move.move_type) AS counterpart_move_types,
                        COALESCE(BOOL_AND(COALESCE(pay.is_matched, FALSE))
                            FILTER (WHERE counterpart_move.origin_payment_id IS NOT NULL), TRUE) AS all_payments_matched,
                        BOOL_OR(COALESCE(BOOL(pay.id), FALSE)) as has_payment,
                        BOOL_OR(COALESCE(BOOL(counterpart_move.statement_line_id), FALSE)) as has_st_line
                    FROM account_partial_reconcile part
                    JOIN account_move_line source_line ON source_line.id = part.%s
                    JOIN account_account account ON account.id = source_line.account_id
                    JOIN account_move_line counterpart_line ON counterpart_line.id = part.%s
                    JOIN account_move counterpart_move ON counterpart_move.id = counterpart_line.move_id
                    LEFT JOIN account_payment pay ON pay.id = counterpart_move.origin_payment_id
                    WHERE source_line.move_id IN %s AND counterpart_line.move_id != source_line.move_id
                    GROUP BY source_line.id, source_line.move_id, account.account_type
                ''', SQL.identifier(source_field), SQL.identifier(counterpart_field), stored_ids))

            payment_data = defaultdict(list)
            for row in self.env.execute_query_dict(SQL(" UNION ALL ").join(queries)):
                payment_data[row['source_move_id']].append(row)
        else:
            payment_data = {}

        for invoice in invoices:
            currency = invoice.currency_id or invoice.company_id.currency_id or self.env.company.currency_id
            reconciliation_vals = payment_data.get(invoice.id, [])

            # Restrict on 'receivable'/'payable' lines for invoices/expense entries.
            reconciliation_vals = [x for x in reconciliation_vals if x['source_line_account_type'] in ('asset_receivable', 'liability_payable')]

            new_pmt_state = 'not_paid'
            if currency.is_zero(invoice.amount_residual):
                if any(x['has_payment'] or x['has_st_line'] for x in reconciliation_vals):

                    # Check if the invoice/expense entry is fully paid or 'in_payment'.
                    if all(x['all_payments_matched'] for x in reconciliation_vals):
                        new_pmt_state = 'paid'
                    else:
                        new_pmt_state = invoice._get_invoice_in_payment_state()

                else:
                    new_pmt_state = 'paid'

                    reverse_move_types = set()
                    for x in reconciliation_vals:
                        for move_type in x['counterpart_move_types']:
                            reverse_move_types.add(move_type)

                    in_reverse = (invoice.move_type in ('in_invoice', 'in_receipt')
                                    and (reverse_move_types == {'in_refund'} or reverse_move_types == {'in_refund', 'entry'}))
                    out_reverse = (invoice.move_type in ('out_invoice', 'out_receipt')
                                    and (reverse_move_types == {'out_refund'} or reverse_move_types == {'out_refund', 'entry'}))
                    misc_reverse = (invoice.move_type in ('entry', 'out_refund', 'in_refund')
                                    and reverse_move_types == {'entry'})
                    if in_reverse or out_reverse or misc_reverse:
                        new_pmt_state = 'reversed'
            elif invoice.state == 'posted' and invoice.matched_payment_ids.filtered(lambda p: not p.move_id and p.state == 'in_process'):
                new_pmt_state = invoice._get_invoice_in_payment_state()
            elif reconciliation_vals:
                new_pmt_state = 'partial'
            elif invoice.state == 'posted' and invoice.matched_payment_ids.filtered(lambda p: not p.move_id and p.state == 'paid'):
                new_pmt_state = invoice._get_invoice_in_payment_state()
            invoice.payment_state = new_pmt_state