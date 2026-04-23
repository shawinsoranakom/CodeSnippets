def _is_eligible_for_early_payment_discount(self, currency, reference_date):
        self.ensure_one()
        payment_terms = self.line_ids.filtered(lambda line: line.display_type == 'payment_term')
        return self.currency_id == currency \
            and self.move_type in self._early_payment_discount_move_types() \
            and self.invoice_payment_term_id.early_discount \
            and (
                not reference_date
                or not self.invoice_date
                or (
                    (existing_discount_date := next(iter(payment_terms)).discount_date)
                    and
                    reference_date <= existing_discount_date
                )
            ) \
            and not (payment_terms.sudo().matched_debit_ids + payment_terms.sudo().matched_credit_ids)