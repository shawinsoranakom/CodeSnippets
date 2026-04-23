def _has_to_be_paid(self):
        self.ensure_one()
        transactions = self.transaction_ids.filtered(lambda tx: tx.state in ('pending', 'authorized', 'done'))
        pending_transactions = transactions.filtered(
            lambda tx: tx.state in {'pending', 'authorized'}
                       and tx.provider_code not in {'none', 'custom'})
        enabled_feature = str2bool(
            self.env['ir.config_parameter'].sudo().get_param(
                'account_payment.enable_portal_payment'
            )
        )
        return enabled_feature and bool(
            (self.amount_residual or not transactions)
            and self.state == 'posted'
            and self.payment_state in ('not_paid', 'in_payment', 'partial')
            and not self.currency_id.is_zero(self.amount_residual)
            and self.amount_total
            and self.move_type == 'out_invoice'
            and not pending_transactions
        )