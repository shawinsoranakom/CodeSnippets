def _reconcile_account_move_lines(self, data):
        # reconcile cash receivable lines
        split_cash_statement_lines = data.get('split_cash_statement_lines')
        combine_cash_statement_lines = data.get('combine_cash_statement_lines')
        split_cash_receivable_lines = data.get('split_cash_receivable_lines')
        combine_cash_receivable_lines = data.get('combine_cash_receivable_lines')
        combine_inv_payment_receivable_lines = data.get('combine_inv_payment_receivable_lines')
        split_inv_payment_receivable_lines = data.get('split_inv_payment_receivable_lines')
        combine_invoice_receivable_lines = data.get('combine_invoice_receivable_lines')
        split_invoice_receivable_lines = data.get('split_invoice_receivable_lines')
        stock_output_lines = data.get('stock_output_lines')
        payment_method_to_receivable_lines = data.get('payment_method_to_receivable_lines')
        payment_to_receivable_lines = data.get('payment_to_receivable_lines')


        all_lines = (
              split_cash_statement_lines
            | combine_cash_statement_lines
            | split_cash_receivable_lines
            | combine_cash_receivable_lines
        )
        all_lines.filtered(lambda line: line.move_id.state != 'posted').move_id._post(soft=False)

        accounts = all_lines.mapped('account_id')
        lines_by_account = [all_lines.filtered(lambda l: l.account_id == account and not l.reconciled) for account in accounts if account.reconcile]
        for lines in lines_by_account:
            lines.with_context(no_cash_basis=True).reconcile()


        for payment_method, lines in payment_method_to_receivable_lines.items():
            receivable_account = self._get_receivable_account(payment_method)
            if receivable_account.reconcile:
                lines.filtered(lambda line: not line.reconciled).with_context(no_cash_basis=True).reconcile()

        for payment, lines in payment_to_receivable_lines.items():
            if payment.partner_id.property_account_receivable_id.reconcile:
                lines.filtered(lambda line: not line.reconciled).with_context(no_cash_basis=True).reconcile()

        # Reconcile invoice payments' receivable lines. But we only do when the account is reconcilable.
        # Though `account_default_pos_receivable_account_id` should be of type receivable, there is currently
        # no constraint for it. Therefore, it is possible to put set a non-reconcilable account to it.
        if self.company_id.account_default_pos_receivable_account_id.reconcile:
            for payment_method in combine_inv_payment_receivable_lines:
                lines = combine_inv_payment_receivable_lines[payment_method] | combine_invoice_receivable_lines.get(payment_method, self.env['account.move.line'])
                lines.filtered(lambda line: not line.reconciled).with_context(no_cash_basis=True).reconcile()

            for payment in split_inv_payment_receivable_lines:
                lines = split_inv_payment_receivable_lines[payment] | split_invoice_receivable_lines.get(payment, self.env['account.move.line'])
                lines.filtered(lambda line: not line.reconciled).with_context(no_cash_basis=True).reconcile()

        return data