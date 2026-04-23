def _prepare_default_reversal(self, move):
        reverse_date = self.date
        mixed_payment_term = move.invoice_payment_term_id.id if move.invoice_payment_term_id.early_pay_discount_computation == 'mixed' else None
        lang = move.partner_id.lang or self.env.lang
        return {
            'ref': self.with_context(lang=lang).env._('Reversal of: %(move_name)s, %(reason)s', move_name=move.name, reason=self.reason)
                   if self.reason
                   else self.with_context(lang=lang).env._('Reversal of: %s', move.name),
            'date': reverse_date,
            'invoice_date_due': reverse_date,
            'invoice_date': move.is_invoice(include_receipts=True) and (self.date or move.date) or False,
            'journal_id': self.journal_id.id,
            'invoice_payment_term_id': mixed_payment_term,
            'invoice_user_id': move.invoice_user_id.id,
            'auto_post': 'at_date' if reverse_date > fields.Date.context_today(self) else 'no',
            'invoice_origin': move.invoice_origin,
        }