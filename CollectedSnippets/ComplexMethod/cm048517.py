def _get_total_amounts_to_pay(self, batch_results):
        self.ensure_one()
        next_payment_date = self._get_next_payment_date_in_context()
        amount_per_line_common = []
        amount_per_line_by_default = []
        amount_per_line_full_amount = []
        amount_per_line_for_difference = []
        epd_applied = False
        first_installment_mode = False
        all_lines = self.env['account.move.line']
        for batch_result in batch_results:
            all_lines |= batch_result['lines']
        all_lines = all_lines.sorted(key=lambda line: (line.move_id, line.date_maturity or date.max))
        for lines in all_lines.grouped('move_id').values():
            installments = lines._get_installments_data(payment_currency=self.currency_id, payment_date=self.payment_date, next_payment_date=next_payment_date)
            last_installment_mode = False
            for installment in installments:
                line = installment['line']
                if installment['type'] == 'early_payment_discount':
                    epd_applied = True
                    amount_per_line_by_default.append(installment)
                    amount_per_line_for_difference.append({
                        **installment,
                        'amount_residual_currency': line.amount_residual_currency,
                        'amount_residual': line.amount_residual,
                    })
                    continue

                # Installments.
                # In case of overdue, all of them are sum as a default amount to be paid.
                # The next installment is added for the difference.
                if (
                    line.display_type == 'payment_term'
                    and installment['type'] in ('overdue', 'next', 'before_date')
                ):
                    if installment['type'] == 'overdue':
                        amount_per_line_common.append(installment)
                    elif installment['type'] == 'before_date':
                        amount_per_line_common.append(installment)
                        first_installment_mode = 'before_date'
                    elif installment['type'] == 'next':
                        if last_installment_mode in ('next', 'overdue', 'before_date'):
                            amount_per_line_full_amount.append(installment)
                        elif not last_installment_mode:
                            amount_per_line_common.append(installment)
                            # if we have several moves and one of them has as first installment, a 'next', we want
                            # the whole batches to have a mode of 'next', overriding an 'overdue' on another move
                            first_installment_mode = 'next'
                    last_installment_mode = installment['type']
                    first_installment_mode = first_installment_mode or last_installment_mode
                    continue

                amount_per_line_common.append(installment)

        common = self._convert_to_wizard_currency(amount_per_line_common)
        by_default = self._convert_to_wizard_currency(amount_per_line_by_default)
        for_difference = self._convert_to_wizard_currency(amount_per_line_for_difference)
        full_amount = self._convert_to_wizard_currency(amount_per_line_full_amount)

        lines = self.env['account.move.line']
        for value in amount_per_line_common + amount_per_line_by_default:
            lines |= value['line']

        return {
            # default amount shown in the wizard (different from full for installments)
            'amount_by_default': abs(common + by_default),
            'full_amount': abs(common + by_default + full_amount),
            # for_difference is used to compute the difference for the Early Payment Discount
            'amount_for_difference': abs(common + for_difference),
            'full_amount_for_difference': abs(common + for_difference + full_amount),
            'epd_applied': epd_applied,
            'installment_mode': first_installment_mode,
            'lines': lines,
        }