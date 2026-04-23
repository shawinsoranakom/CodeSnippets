def _get_installments_data(self, payment_currency=None, payment_date=None, next_payment_date=None):
        move = self.move_id
        move.ensure_one()

        payment_date = payment_date or fields.Date.context_today(self)

        term_lines = self.sorted(key=lambda line: (line.date_maturity or date.max, line.date))
        sign = move.direction_sign
        installments = []
        first_installment_mode = False
        current_installment_mode = False
        for i, line in enumerate(term_lines, start=1):
            installment = {
                'number': i,
                'line': line,
                'date_maturity': line.date_maturity or line.date,
                'amount_residual_currency': line.amount_residual_currency,
                'amount_residual': line.amount_residual,
                'amount_residual_currency_unsigned': -sign * line.amount_residual_currency,
                'amount_residual_unsigned': -sign * line.amount_residual,
                'type': 'other',
                'reconciled': line.reconciled,
            }
            installments.append(installment)

            # Already reconciled.
            if line.reconciled:
                continue

            # Early payment discount.
            # In that case, we want to report the difference of the epd and display it on the UI.
            if move._is_eligible_for_early_payment_discount(payment_currency or line.currency_id, payment_date):
                installment.update({
                    'amount_residual_currency': line.discount_amount_currency,
                    'amount_residual': line.discount_balance,
                    'amount_residual_currency_unsigned': -sign * line.discount_amount_currency,
                    'amount_residual_unsigned': -sign * line.discount_balance,
                    'discount_amount_currency': line.amount_currency - line.discount_amount_currency,
                    'discount_amount': line.balance - line.discount_balance,
                    'type': 'early_payment_discount',
                })
                continue

            # Installments.
            # In case of overdue, all of them are sum as a default amount to be paid.
            # The next installment is added for the difference.
            if line.display_type == 'payment_term':
                if next_payment_date and (line.date_maturity or line.date) <= next_payment_date:
                    current_installment_mode = 'before_date'
                elif (line.date_maturity or line.date) < payment_date:
                    # Collect all overdue installments.
                    first_installment_mode = current_installment_mode = 'overdue'
                elif not first_installment_mode:
                    # Suggest the next installment in case of no overdue.
                    first_installment_mode = 'next'
                    current_installment_mode = 'next'
                elif current_installment_mode == 'overdue':
                    # After an overdue, just add the next installment for the difference.
                    current_installment_mode = 'next'
                installment['type'] = current_installment_mode

        return installments