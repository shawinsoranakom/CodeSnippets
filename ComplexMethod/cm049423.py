def _l10n_es_edi_facturae_get_refunded_invoices(self):
        self.env['account.partial.reconcile'].flush_model()
        invoices_refunded_mapping = {invoice.id: invoice.reversed_entry_id.id for invoice in self}

        stored_ids = tuple(self.ids)
        queries = []
        for source_field, counterpart_field in (
            ('debit_move_id', 'credit_move_id'),
            ('credit_move_id', 'debit_move_id'),
        ):
            queries.append(SQL('''
                SELECT
                    source_line.move_id AS source_move_id,
                    counterpart_line.move_id AS counterpart_move_id
                FROM account_partial_reconcile part
                JOIN account_move_line source_line ON source_line.id = part.%s
                JOIN account_move_line counterpart_line ON counterpart_line.id = part.%s
                WHERE source_line.move_id IN %s AND counterpart_line.move_id != source_line.move_id
                GROUP BY source_move_id, counterpart_move_id
            ''', SQL.identifier(source_field), SQL.identifier(counterpart_field), stored_ids))
        payment_data = defaultdict(list)
        for row in self.env.execute_query_dict(SQL(" UNION ALL ").join(queries)):
            payment_data[row['source_move_id']].append(row)

        for invoice in self:
            if not invoice.move_type.endswith('refund'):
                # We only want to map refunds
                continue

            for move_id in (record_dict['counterpart_move_id'] for record_dict in payment_data.get(invoice.id, [])):
                invoices_refunded_mapping[invoice.id] = move_id
        return invoices_refunded_mapping