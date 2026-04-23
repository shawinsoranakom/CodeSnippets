def _compute_state(self):
        for payment in self:
            if not payment.state:
                payment.state = 'draft'
            # in_process --> paid
            if (move := payment.move_id) and payment.state in ('paid', 'in_process'):
                liquidity, _counterpart, _writeoff = payment._seek_for_lines()
                payment.state = (
                    'paid'
                    if move.company_currency_id.is_zero(sum(liquidity.mapped('amount_residual'))) or not any(liquidity.account_id.mapped('reconcile')) else
                    'in_process'
                )
            if payment.state == 'in_process' and (moves := (payment.reconciled_invoice_ids | payment.reconciled_bill_ids)) and all(invoice.payment_state == 'paid' for invoice in moves):
                payment.state = 'paid'