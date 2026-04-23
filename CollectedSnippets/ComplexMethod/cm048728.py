def _compute_amount_residual(self):
        """ Computes the residual amount of a move line from a reconcilable account in the company currency and the line's currency.
            This amount will be 0 for fully reconciled lines or lines from a non-reconcilable account, the original line amount
            for unreconciled lines, and something in-between for partially reconciled lines.
        """
        need_residual_lines = self.filtered(lambda x: x.account_id.reconcile or x.account_id.account_type in ('asset_cash', 'liability_credit_card'))
        # Run the residual amount computation on all lines stored in the db. By
        # using _origin, new records (with a NewId) are excluded and the
        # computation works automagically for virtual onchange records as well.
        stored_lines = need_residual_lines._origin

        if stored_lines:
            self.env['account.partial.reconcile'].flush_model()
            self.env['res.currency'].flush_model(['decimal_places'])

            aml_ids = tuple(stored_lines.ids)
            self.env.cr.execute('''
                SELECT
                    part.debit_move_id AS line_id,
                    'debit' AS flag,
                    COALESCE(SUM(part.amount), 0.0) AS amount,
                    ROUND(SUM(part.debit_amount_currency), curr.decimal_places) AS amount_currency
                FROM account_partial_reconcile part
                JOIN res_currency curr ON curr.id = part.debit_currency_id
                WHERE part.debit_move_id IN %s
                GROUP BY part.debit_move_id, curr.decimal_places
                UNION ALL
                SELECT
                    part.credit_move_id AS line_id,
                    'credit' AS flag,
                    COALESCE(SUM(part.amount), 0.0) AS amount,
                    ROUND(SUM(part.credit_amount_currency), curr.decimal_places) AS amount_currency
                FROM account_partial_reconcile part
                JOIN res_currency curr ON curr.id = part.credit_currency_id
                WHERE part.credit_move_id IN %s
                GROUP BY part.credit_move_id, curr.decimal_places
            ''', [aml_ids, aml_ids])
            amounts_map = {
                (line_id, flag): (amount, amount_currency)
                for line_id, flag, amount, amount_currency in self.env.cr.fetchall()
            }
        else:
            amounts_map = {}

        # Lines that can't be reconciled with anything since the account doesn't allow that.
        for line in self - need_residual_lines:
            line.amount_residual = 0.0
            line.amount_residual_currency = 0.0
            line.reconciled = False

        for line in need_residual_lines:
            # Since this part could be call on 'new' records, 'company_currency_id'/'currency_id' could be not set.
            comp_curr = line.company_currency_id or self.env.company.currency_id
            foreign_curr = line.currency_id or comp_curr

            # Retrieve the amounts in both foreign/company currencies. If the record is 'new', the amounts_map is empty.
            debit_amount, debit_amount_currency = amounts_map.get((line._origin.id, 'debit'), (0.0, 0.0))
            credit_amount, credit_amount_currency = amounts_map.get((line._origin.id, 'credit'), (0.0, 0.0))

            # Subtract the values from the account.partial.reconcile to compute the residual amounts.
            line.amount_residual = comp_curr.round(line.balance - debit_amount + credit_amount)
            line.amount_residual_currency = foreign_curr.round(line.amount_currency - debit_amount_currency + credit_amount_currency)
            line.reconciled = (
                comp_curr.is_zero(line.amount_residual)
                and foreign_curr.is_zero(line.amount_residual_currency)
            )