def _get_receivable_lines_for_invoice_reconciliation(self, receivable_account):
        """
        If this payment is linked to an account.move, this returns the corresponding receivable lines
        that should be reconciled with the invoice's receivable lines.
        The introduced heuristics here is important for cases where the pos receivable account is the same
        as the receivable account of the customer.

        - positive payment -> negative balance lines
        - negative payment -> positive balance lines
        """

        result = self.env['account.move.line']
        for payment in self:
            if not payment.account_move_id:
                continue

            currency = payment.currency_id
            is_positive_amount = currency.compare_amounts(payment.amount, 0) > 0

            for line in payment.account_move_id.line_ids:
                if currency.compare_amounts(line.balance, 0) == 0 or line.account_id != receivable_account or line.reconciled:
                    continue

                if is_positive_amount:
                    if currency.compare_amounts(line.balance, 0) < 0:
                        result |= line
                else:
                    if currency.compare_amounts(line.balance, 0) > 0:
                        result |= line

        return result