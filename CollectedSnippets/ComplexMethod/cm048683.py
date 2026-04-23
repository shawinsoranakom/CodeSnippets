def _get_invoice_next_payment_values(self, custom_amount=None):
        self.ensure_one()
        term_lines = self.line_ids.filtered(lambda line: line.display_type == 'payment_term')
        if not term_lines:
            return {}
        installments = term_lines._get_installments_data()
        not_reconciled_installments = [x for x in installments if not x['reconciled']]
        overdue_installments = [x for x in not_reconciled_installments if x['type'] == 'overdue']
        # Early payment discounts can only have one installment at most
        epd_installment = next((installment for installment in installments if installment['type'] == 'early_payment_discount'), {})
        show_installments = len(installments) > 1
        additional_info = {}

        if show_installments and overdue_installments:
            installment_state = 'overdue'
            amount_due = self.amount_residual
            next_amount_to_pay = sum(x['amount_residual_currency_unsigned'] for x in overdue_installments)
            next_payment_reference = f"{self.name}-{overdue_installments[0]['number']}"
            next_due_date = overdue_installments[0]['date_maturity']
        elif show_installments and not_reconciled_installments:
            installment_state = 'next'
            amount_due = self.amount_residual
            next_amount_to_pay = not_reconciled_installments[0]['amount_residual_currency_unsigned']
            next_payment_reference = f"{self.name}-{not_reconciled_installments[0]['number']}"
            next_due_date = not_reconciled_installments[0]['date_maturity']
        elif epd_installment:
            installment_state = 'epd'
            amount_due = epd_installment['amount_residual_currency_unsigned']
            next_amount_to_pay = self.amount_residual
            next_payment_reference = self.name
            next_due_date = epd_installment['date_maturity']
            discount_date = epd_installment['line'].discount_date or fields.Date.context_today(self)
            discount_amount_currency = epd_installment['discount_amount_currency']
            days_left = max(0, (discount_date - fields.Date.context_today(self)).days)  # should never be lower than 0 since epd is valid
            if days_left > 0:
                discount_msg = _(
                    "Discount of %(amount)s if paid within %(days)s days",
                    amount=self.currency_id.format(discount_amount_currency),
                    days=days_left,
                )
            else:
                discount_msg = _(
                    "Discount of %(amount)s if paid today",
                    amount=self.currency_id.format(discount_amount_currency),
                )

            additional_info.update({
                'epd_discount_amount_currency': discount_amount_currency,
                'epd_discount_amount': epd_installment['discount_amount'],
                'discount_date': fields.Date.to_string(discount_date),
                'epd_days_left': days_left,
                'epd_line': epd_installment['line'],
                'epd_discount_msg': discount_msg,
            })
        else:
            installment_state = None
            amount_due = self.amount_residual
            next_amount_to_pay = self.amount_residual
            next_payment_reference = self.name
            next_due_date = self.invoice_date_due

        if custom_amount is not None:
            is_custom_amount_same_as_next_amount = self.currency_id.is_zero(custom_amount - next_amount_to_pay)
            is_custom_amount_same_as_epd_discounted_amount = installment_state == 'epd' and self.currency_id.is_zero(custom_amount - amount_due)
            if not is_custom_amount_same_as_next_amount and not is_custom_amount_same_as_epd_discounted_amount:
                installment_state = 'next'
                next_amount_to_pay = custom_amount
                next_payment_reference = self.name
                next_due_date = installments[0]['date_maturity']

        return {
            'payment_state': self.payment_state,
            'installment_state': installment_state,
            'next_amount_to_pay': next_amount_to_pay,
            'next_payment_reference': next_payment_reference,
            'amount_paid': self.amount_total - self.amount_residual,
            'amount_due': amount_due,
            'next_due_date': next_due_date,
            'due_date': self.invoice_date_due,
            'not_reconciled_installments': not_reconciled_installments,
            'is_last_installment': len(not_reconciled_installments) == 1,
            **additional_info,
        }